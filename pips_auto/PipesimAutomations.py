import os
import sys
import pandas as pd
import time, datetime
from sixgill.pipesim import Model, ModelComponents, Units, Parameters
from sixgill.definitions import SystemVariables, ProfileVariables


class UnitsConverter:
    class Pressure:
        def bara_to_kgfpcm2(pressure_bara: float):
            return pressure_bara * 1.0197162129779282 - 1.033227
        def kgfpcm2g_to_bara(pressure_kgfpcm2: float):
            return (pressure_kgfpcm2 + 1.033227) / 1.0197162129779282
        def psi_to_kgfpcm2(pressure_psi: float):
            return pressure_psi * 0.0703069579640175
    class Flowrate:
        def sm3pday_to_sm3pyear(flowrate_sm3pday: float):
            return flowrate_sm3pday * 365


def get_importfiles_names(directory: str):
    all_filenames = os.listdir(directory)
    importfiles_names_list = []
    for filename in all_filenames:
        if filename[-5:] == '.xlsx' and 'RegimesImport' in filename:
            importfiles_names_list.append(filename)
    return importfiles_names_list


def get_models_names(directory: str):
    all_filenames = os.listdir(directory)
    models_names_list = []
    for filename in all_filenames:
        if filename[-5:] == '.pips':
            models_names_list.append(filename)
    return models_names_list


def select_importfile(importfiles_names_list: list):
    print('Select importfile from listed below:')
    for i in range(len(importfiles_names_list)):
        print('{} -\t{}'.format(i + 1, importfiles_names_list[i]))
    print('Input importfile name number:')
    selected_number = int(input())
    selected_importfile = importfiles_names_list[selected_number - 1]
    print('SELECTED IMPORTFILE:\t{}\n'.format(selected_importfile))
    return selected_importfile


def select_model(models_names_list: list):
   print('Select model from listed below:')
   for i in range(len(models_names_list)):
       print('{} -\t{}'.format(i + 1, models_names_list[i]))
   print('Input model name number:')
   selected_number = int(input())
   selected_model = models_names_list[selected_number - 1]
   print('SELECTED MODEL:\t{}\n'.format(selected_model))
   return selected_model


def set_source_flowrate_boundaries(model: Model,
                                   source_name: str,
                                   liquid_flowrate,
                                   watercut,
                                   GOR):
        model.set_value(Source= source_name,
                        parameter= Parameters.Source.OVERRIDESINITIALIZED,
                        value= True)
        model.set_value(Source= source_name,
                        parameter= Parameters.Source.LIQUIDFLOWRATE,
                        value= liquid_flowrate)
        model.set_value(Source= source_name,
                        parameter= Parameters.Source.WATERCUT,
                        value= watercut)
        if GOR != 'std':
            model.set_value(Source= source_name,
                            parameter= Parameters.Source.GOR,
                            value= GOR)


def set_start_simulation(model: Model):
    RESULT_VARIABLES_SYSTEM = [SystemVariables.PRESSURE,
                               SystemVariables.GOR_STOCKTANK,
                               SystemVariables.VOLUME_FLOWRATE_GAS_STOCKTANK,
                               SystemVariables.VOLUME_FLOWRATE_LIQUID_STOCKTANK,
                               SystemVariables.VOLUME_FLOWRATE_OIL_STOCKTANK,
                               SystemVariables.VOLUME_FLOWRATE_WATER_STOCKTANK,
                               SystemVariables.WATER_CUT_STOCKTANK,
                               SystemVariables.FLOWING_GAS_VOLUME_FLOWRATE,
                               SystemVariables.LIQUID_RATE,
                               SystemVariables.VOLUME_FLOWRATE_LIQUID_INSITU,
                               SystemVariables.MAXIMUM_VELOCITY_LIQUID,
                               SystemVariables.MAXIMUM_VELOCITY_GAS,
                               SystemVariables.VELOCITY_GAS]
    RESULT_VARIABLES_PROFILE = [ProfileVariables.VELOCITY_GAS,
                                ProfileVariables.HOLDUP_FRACTION_LIQUID]
    model.tasks.networksimulation.reset_conditions()
    print('Running simulation...')
    results = model.tasks.networksimulation.run(system_variables= RESULT_VARIABLES_SYSTEM,
                                                profile_variables= RESULT_VARIABLES_PROFILE)
    print('Simulation completed\nCalculated pressures: {}'.format(results.node[SystemVariables.PRESSURE]))
    return results


def get_max_velocity_gas_for_network(network_simulation_result):
    max_velocity_gas_dict = results.system[SystemVariables.MAXIMUM_VELOCITY_GAS]
    max_velocity_gas_dict.pop('Unit')
    return max(max_velocity_gas_dict.values())


def get_min_velocity_gas_for_network(network_simulation_result):
    min_velocity_gas = 999
    for branch, profile in results.profile.items():
        aux_profile_result_df = pd.DataFrame.from_dict(profile)
        if min(aux_profile_result_df['VelocityGas']) < min_velocity_gas:
            min_velocity_gas = min(aux_profile_result_df['VelocityGas'])
    return min_velocity_gas


def get_max_velocity_liquid_for_network(network_simulation_result):
    max_velocity_liquid_dict = results.system[SystemVariables.MAXIMUM_VELOCITY_LIQUID]
    max_velocity_liquid_dict.pop('Unit')
    return max(max_velocity_liquid_dict.values())


def save_DataFrame_to_excel_with_warnings(df: pd.DataFrame,
                                          file_name: str):
    try:
        print('Saving results to {}...'.format(file_name))
        df.to_excel(file_name, index= False)
    except:
        print('Check {} file and close it it is open. Press "enter" to continue...'.format(file_name))
        input()
        try:
            print('Saving results to {}...'.format(file_name))
            df.to_excel(file_name, index=False)
        except:
            print('Failed to access {} file! Results would not be saved.'.format(file_name))