import os
import sys
import pandas as pd
import time, datetime
from sixgill.pipesim import Model, ModelComponents, Units, Parameters
from sixgill.definitions import SystemVariables, ProfileVariables
import PipesimAutomations as PA
##############################################################################

cwd = os.getcwd()
model_names_list = PA.get_models_names(cwd)
model_name = PA.select_model(model_names_list)
importfiles_names_list = PA.get_importfiles_names(cwd)
importfile_name = PA.select_importfile(importfiles_names_list)

start_time = time.time()

import_df = pd.read_excel(importfile_name)

model = Model.open(model_name, units= Units.METRIC)

output_df = pd.DataFrame(columns= ['Date', 'Well', 'ST Liquid flowrate, sm3/d', 'WC, %', 'ST Oil flowrate, sm3/d',
                                   'ST Water flowrate, sm3/d', 'GOR, sm3/m3', 'ST Gas flowrate, mmsm3/d',
                                   'Pressure at source, kgf/cm2', 'Pressure at sink, kgf/cm2',
                                   'MAX Liquid velocity, m/s', 'MAX Gas velocity, m/s',
                                   'MIN Gas velocity, m/s'])

in_situ_flowrates_at_sink_output_df = pd.DataFrame(columns= ['Date', 'FL Gas rate, m3/d', 'FL Liquid rate, m3/d'])
problems_counter = 0

for date in import_df['Дата'].unique():
    print('Staring calculations for {}...'.format(date))
    model.set_all_value(component=ModelComponents.SOURCE, parameter=Parameters.Source.ISACTIVE, value=False)
    df_for_single_date = import_df.loc[import_df['Дата'] == date]
    active_wells = []
    sink = str(model.find_components(component=ModelComponents.SINK)[0])
    for well in df_for_single_date['Скважина']:
        well_index = df_for_single_date.loc[df_for_single_date['Скважина'] == well].index.values
        if df_for_single_date.loc[well_index[0]]['Жидкость, м3/сут'] > 0:
            source = model.find(Source= well)[0]
            active_wells.append(source)
            model.set_value(Source= source, parameter= Parameters.Source.ISACTIVE, value= True)
            PA.set_source_flowrate_boundaries(model= model,
                                           source_name= source,
                                           liquid_flowrate= df_for_single_date.loc[well_index[0]]['Жидкость, м3/сут'],
                                           watercut= df_for_single_date.loc[well_index[0]]['Обводненность, %'],
                                           GOR= df_for_single_date.loc[well_index[0]]['Газовый фактор, м3/м3'])
    results = PA.set_start_simulation(model)
    try:
        for well in active_wells:
            well_index = df_for_single_date.loc[df_for_single_date['Скважина'] == well].index.values
            output_df = output_df.append({'Date': date,
                                          'Well': well,
                                          'ST Liquid flowrate, sm3/d': results.node[SystemVariables.VOLUME_FLOWRATE_LIQUID_STOCKTANK][well],
                                          'WC, %': results.node[SystemVariables.WATER_CUT_STOCKTANK][well],
                                          'ST Oil flowrate, sm3/d': results.node[SystemVariables.VOLUME_FLOWRATE_OIL_STOCKTANK][well],
                                          'ST Water flowrate, sm3/d': results.node[SystemVariables.VOLUME_FLOWRATE_WATER_STOCKTANK][well],
                                          'GOR, sm3/m3': results.node[SystemVariables.GOR_STOCKTANK][well],
                                          'ST Gas flowrate, mmsm3/d': results.node[SystemVariables.VOLUME_FLOWRATE_GAS_STOCKTANK][well],
                                          'Pressure at source, kgf/cm2': PA.UnitsConverter.Pressure.bara_to_kgfpcm2(results.node[SystemVariables.PRESSURE][well]), # давление на стоке не всегда нужно
                                          'Pressure at sink, kgf/cm2': PA.UnitsConverter.Pressure.bara_to_kgfpcm2(results.node[SystemVariables.PRESSURE][sink]), # давление на стоке не всегда нужно
                                          'MAX Liquid velocity, m/s': PA.get_max_velocity_liquid_for_network(results),
                                          'MAX Gas velocity, m/s': PA.get_max_velocity_gas_for_network(results),
                                          'MIN Gas velocity, m/s': PA.get_min_velocity_gas_for_network(results)},
                                         ignore_index= True)
    except:
        print('Problem in sources results writing down for {}!'.format(date))
        problems_counter += 1

    try:
        in_situ_flowrates_at_sink_output_df = in_situ_flowrates_at_sink_output_df.append({'Date': date,
                                                                                          'FL Gas rate, m3/d': results.node[SystemVariables.FLOWING_GAS_VOLUME_FLOWRATE][sink],
                                                                                          'FL Liquid rate, m3/d': results.node[SystemVariables.VOLUME_FLOWRATE_LIQUID_INSITU][sink]},
                                                                                         ignore_index= True)
    except:
        print('Problem in sinks results writing down for {}!'.format(date))
        problems_counter += 1
    print('Execution time is {:.2f} seconds\n'.format(time.time() - start_time))

print('Execution finished at {}'.format(datetime.datetime.utcfromtimestamp(time.time() + 10800)))
print('Total execution time is {:.2f} seconds'. format(time.time() - start_time))
print('Problems with writing down results: {}'.format(problems_counter))
print()
PA.save_DataFrame_to_excel_with_warnings(output_df, 'RESULT.xlsx')
PA.save_DataFrame_to_excel_with_warnings(in_situ_flowrates_at_sink_output_df, 'RESULT_IN_SITU_FLOWRATES_AT_SINK.xlsx')


# Add 'OpenPipesimUI at selected date option