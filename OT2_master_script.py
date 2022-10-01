from opentrons import protocol_api
import json

# metadata
metadata = {
    "protocolName": "PCR Compliation v1",
    "author": "Alex Perkins",

    "email": "a.j.p.perkins@sms.ed.ac.uk",
    "description": "First draft of script to compile PCR rxns",
    "apiLevel": "2.5",
}

#
# Protocol run function. the part after the colon lets your editor know
# where to look for autocomplete suggestions
def run(protocol: protocol_api.ProtocolContext):

    # 0. Reading in json setting files-----------------------------------------


    # Defining the file paths of raspberry pi
    experiment_settings_dict_path = "/data/user_storage/"+ experiment_prefix + "/" + experiment_prefix + "_experiment_settings.json"
    labware_settings_dict_path = "/data/user_storage/"+ experiment_prefix + "/" + experiment_prefix + "_labware_settings.json"
    pipetting_settings_dict_path = "/data/user_storage/" + experiment_prefix + "/" + experiment_prefix + "_pipetting_settings.json"
    reagent_sources_dict_path = "/data/user_storage/" + experiment_prefix + "/" + experiment_prefix + "_reagent_sources.json"

    # Reading in json json_settings_file
    experiment_settings_dict = json.load(open(experiment_settings_dict_path, 'r'))
    protocol.comment("Experiment settings json file was read in")

    labware_settings_dict = json.load(open(labware_settings_dict_path, 'r'))
    protocol.comment("Labware settings json file was read in")

    pipetting_settings_dict = json.load(open(pipetting_settings_dict_path, 'r'))
    protocol.comment("Pipetting settings json file was read in")

    reagent_sources_dict = json.load(open(reagent_sources_dict_path, 'r'))
    protocol.comment("Reagent Sources json file was read in")

    # 1. Defining variables used in protocol-----------------------------------


    # labware

    # Defining the temperature module
    temperature_module = protocol.load_module(labware_settings_dict["temp_module"]["name"], labware_settings_dict["temp_module"]["deck_position"])


    # Defining the pcr plate ontop of the temperature module
    # https://www.bio-rad.com/en-uk/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601
    pcr_tubes = temperature_module.load_labware(
        labware_settings_dict["pcr_temp_plate"]["name"],
        label="Temperature-Controlled Tubes",
    )

    protocol.comment(str(labware_settings_dict["nunc_384"]["offsets"]["x"]))

    pcr_tubes.set_offset(x = labware_settings_dict["pcr_temp_plate"]["offsets"]["x"],
                              y = labware_settings_dict["pcr_temp_plate"]["offsets"]["y"],
                              z = labware_settings_dict["pcr_temp_plate"]["offsets"]["z"])



    # Defining the 1.5ul eppendorf rack
    eppendorf_1500ul_x24_rack = protocol.load_labware(
        labware_settings_dict["eppendorf_1500ul_x24_rack"]["name"], labware_settings_dict["eppendorf_1500ul_x24_rack"]["deck_position"]
    )

    eppendorf_1500ul_x24_rack.set_offset(x = labware_settings_dict["eppendorf_1500ul_x24_rack"]["offsets"]["x"],
                                  y = labware_settings_dict["eppendorf_1500ul_x24_rack"]["offsets"]["y"],
                                  z = labware_settings_dict["eppendorf_1500ul_x24_rack"]["offsets"]["z"])



    # Defining the 20ul tip rack
    tiprack_20ul = protocol.load_labware(labware_settings_dict["tiprack_20ul"]["name"], labware_settings_dict["tiprack_20ul"]["deck_position"])

    tiprack_20ul.set_offset(x = labware_settings_dict["tiprack_20ul"]["offsets"]["x"],
                                  y = labware_settings_dict["tiprack_20ul"]["offsets"]["y"],
                                  z = labware_settings_dict["tiprack_20ul"]["offsets"]["z"])


    # Defining left_pipette (p20)
    left_pipette = protocol.load_instrument(
        labware_settings_dict["left_pipette"]["name"], "left", tip_racks=[tiprack_20ul]
    )

    # Defining the 300ul tip rack
    tiprack_300ul = protocol.load_labware(labware_settings_dict["tiprack_300ul"]["name"], labware_settings_dict["tiprack_300ul"]["deck_position"])

    tiprack_300ul.set_offset(x = labware_settings_dict["tiprack_300ul"]["offsets"]["x"],
                                  y = labware_settings_dict["tiprack_300ul"]["offsets"]["y"],
                                  z = labware_settings_dict["tiprack_300ul"]["offsets"]["z"])


    # Defining right_pipette (p300)
    right_pipette = protocol.load_instrument(
        labware_settings_dict["right_pipette"]["name"], "right", tip_racks=[tiprack_300ul]
    )

    # 2. Defining functions used in this protocol------------------------------

    # distributing_components_to_master_mix_from_stock
    def distributing_components_to_master_mix_from_stock(master_mix_well, components_source_well, lysate_aspirate_height):

        left_pipette.pick_up_tip()

        left_pipette.well_bottom_clearance.aspirate = substrates_aspirate_height
        left_pipette.well_bottom_clearance.dispense = pipetting_settings_dict["substrates_dispense_well_bottom_clearance"]

        # aspirate step
        left_pipette.aspirate(pipetting_settings_dict["substrates_aspirate_volume"], source_well, rate=pipetting_settings_dict["substrates_aspirate_rate"])
        left_pipette.move_to(source_well.top(-2))
        left_pipette.touch_tip()

        # Dispense Step
        left_pipette.dispense(pipetting_settings_dict["substrates_dispense_volume"], nunc_384[well], rate=pipetting_settings_dict["substrates_dispense_rate"])

        left_pipette.drop_tip()


    # 3. Running protocol------------------------------------------------------


    # Set temperature of temperature module to 4 degrees. The protocol will pause
    # until this is reached.
    #temperature_module.set_temperature(4)

    # Extracting the different experiments from the experiments

    # settings file
    experiment_ids = experiment_settings_dict.keys()

    # Master Mix Compilation
    protocol.comment("Beginning Master Mix Compilations...")




    # Looping through the different experiments
    for experiment_id in experiment_ids:

        # Defining the source well for the substrates master mix
        substrates_source_well = pcr_temp_plate[experiment_settings_dict[experiment_id]["substrates_source_well"]]

        # Defining a list of wells for dispensing
        dispense_well_list = experiment_settings_dict[experiment_id]["dispense_well_list"]

        # Defining the initial lysate aspiration height
        substrates_aspirate_height = pipetting_settings_dict["substrates_aspirate_height_init"]

        # Dispensing substrates into each of the wells in dispense well list
        for well in dispense_well_list:

            # Caliing function to distribute substrates
            distribute_substrates(
                well, substrates_source_well, substrates_aspirate_height
            )

            # Reducing the aspiration height by subsrates_aspirate_height_inc
            substrates_aspirate_height -= pipetting_settings_dict["substrates_aspirate_height_inc"]


        protocol.comment("Substrate dispense step complete for experiment " + experiment_id)


    protocol.comment(" ")
    protocol.comment("Master Mix compliations complete.")
    # Pausing protocol so the plate can be span down in the centrifuge before

    # Turning off temp module after all experiments have finished
    temperature_module.deactivate()
