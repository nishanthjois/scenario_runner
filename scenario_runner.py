#!/usr/bin/env python

# Copyright (c) 2018-2019 Intel Labs.
# authors: Fabian Oboril (fabian.oboril@intel.com)
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Welcome to CARLA scenario_runner

This is the main script to be executed when running a scenario.
It loeads the scenario coniguration, loads the scenario and manager,
and finally triggers the scenario execution.
"""

from __future__ import print_function
import argparse
from argparse import RawTextHelpFormatter
import random
import sys

import carla

from Scenarios.follow_leading_vehicle import *
from Scenarios.opposite_vehicle_taking_priority import *
from Scenarios.object_crash_vehicle import *
from Scenarios.no_signal_junction_crossing import *
from Scenarios.object_crash_intersection import *
from Scenarios.control_loss import *
from Scenarios.config_parser import *
from ScenarioManager.scenario_manager import ScenarioManager


# Version of scenario_runner
VERSION = 0.2


# Dictionary of all supported scenarios.
# key = Name of config file in Configs/
# value = List as defined in the scenario module
SCENARIOS = {
    "FollowLeadingVehicle": FOLLOW_LEADING_VEHICLE_SCENARIOS,
    "ObjectCrossing": OBJECT_CROSSING_SCENARIOS,
    "RunningRedLight": RUNNING_RED_LIGHT_SCENARIOS,
    "NoSignalJunction": NO_SIGNAL_JUNCTION_SCENARIOS,
    "VehicleTurning": TURNING_SCENARIOS,
    "ControlLoss": CONTROL_LOSS_SCENARIOS
}


def setup_vehicle(world, model, spawn_point, hero=False):
    """
    Function to setup the most relevant vehicle parameters,
    incl. spawn point and vehicle model.
    """
    blueprint_library = world.get_blueprint_library()

    # Get vehicle by model
    blueprint = random.choice(blueprint_library.filter(model))
    if hero:
        blueprint.set_attribute('role_name', 'hero')
    else:
        blueprint.set_attribute('role_name', 'scenario')

    vehicle = world.try_spawn_actor(blueprint, spawn_point)

    if vehicle is None:
        raise Exception(
            "Error: Unable to spawn vehicle {} at {}".format(model, spawn_point))
    else:
        # Let's deactivate the autopilot of the vehicle
        vehicle.set_autopilot(False)

    return vehicle


def get_scenario_class_or_fail(scenario):
    """
    Get scenario class by scenario name
    If scenario is not supported or not found, raise an exception
    """

    for scenarios in SCENARIOS.values():
        if scenario in scenarios:
            if scenario in globals():
                return globals()[scenario]

    raise Exception("Scenario '{}' not supported".format(scenario))


def cleanup(actors):
    """
    Remove and destroy all actors
    """

    for actor in actors:
        if actor is not None:
            actor.destroy()
            actor = None


# TODO: Convert to class
def main(args):
    """
    Main function starting a CARLA client and connecting to the world.
    """

    # Tunable parameters
    client_timeout = 2.0   # in seconds
    wait_for_world = 10.0  # in seconds

    # CARLA world and scenario handlers
    world = None
    scenario = None
    manager = None

    # CARLA actors
    ego_vehicle = None
    other_actors = []

    try:
        # First of all, we need to create the client that will send the requests
        # to the simulator. Here we'll assume the simulator is accepting
        # requests in the localhost at port 2000.
        client = carla.Client(args.host, int(args.port))
        client.set_timeout(client_timeout)

        # Once we have a client we can retrieve the world that is currently
        # running.
        world = client.get_world()

        # Wait for the world to be ready
        world.wait_for_tick(wait_for_world)

        # Create scenario manager
        manager = ScenarioManager(world, args.debug)

        # Setup and run the scenarios for repetition times
        for i in range(int(args.repetitions)):

            # Load the scenario configurations provided in the config file
            scenario_configurations = parse_scenario_configuration(world, args.scenario)

            # Execute each configuration
            # TODO: Also allow execution of single scenarios
            for config in scenario_configurations:
                print("Preparing scenario: " + config.name)

                try:
                    scenario_class = get_scenario_class_or_fail(config.name)
                except:
                    print("Unsupported scenario: " + config.name)
                    continue

                # spawn all required actors
                ego_vehicle = setup_vehicle(
                    world, config.ego_vehicle.model, config.ego_vehicle.transform, hero=True)

                for other_vehicle in config.other_vehicles:
                    other_actors.append(
                        setup_vehicle(world, other_vehicle.model, other_vehicle.transform))

                # Get scenario
                try:
                    scenario = scenario_class(world, ego_vehicle, other_actors, config.town, args.debug)
                except:
                    print("The scenario cannot be loaded")
                    cleanup(other_actors + [ego_vehicle])
                    other_actors = []
                    ego_vehicle = None
                    continue

                # Load scenario and run it
                manager.load_scenario(scenario)
                manager.run_scenario()

                # Provide outputs if required
                junit_filename = None
                if args.junit is not None:
                    junit_filename = args.junit.split(
                        ".")[0] + "_{}.xml".format(i)

                if not manager.analyze_scenario(
                        args.output, args.filename, junit_filename):
                    print("Success!")
                else:
                    print("Failure!")

                # Stop scenario and cleanup
                manager.stop_scenario()
                del scenario

                cleanup(other_actors + [ego_vehicle])
                other_actors = []
                ego_vehicle = None

            print("No more scenarios .... Exiting")

    finally:
        cleanup(other_actors + [ego_vehicle])
        if manager is not None:
            del manager
        if world is not None:
            del world


if __name__ == '__main__':

    DESCRIPTION = ("CARLA Scenario Runner: Setup, Run and Evaluate scenarios using CARLA\n"
                   "Current version: " + str(VERSION))

    PARSER = argparse.ArgumentParser(description=DESCRIPTION,
                                     formatter_class=RawTextHelpFormatter)
    PARSER.add_argument('--host', default='localhost',
                        help='IP of the host server (default: localhost)')
    PARSER.add_argument('--port', default='2000',
                        help='TCP port to listen to (default: 2000)')
    PARSER.add_argument('--debug', action="store_true", help='Run with debug output')
    PARSER.add_argument('--output', action="store_true", help='Provide results on stdout')
    PARSER.add_argument('--filename', help='Write results into given file')
    PARSER.add_argument('--junit', help='Write results into the given junit file')
    PARSER.add_argument('--scenario', help='Name of the scenario to be executed')
    PARSER.add_argument('--repetitions', default=1, help='Number of scenario executions')
    PARSER.add_argument('--list', action="store_true", help='List all supported scenarios and exit')
    PARSER.add_argument('-v', '--version', action='version', version='%(prog)s ' + str(VERSION))
    ARGUMENTS = PARSER.parse_args()

    if ARGUMENTS.list:
        print("Currently the following scenarios are supported:")
        print(*SCENARIOS.keys(), sep='\n')
        sys.exit(0)

    if ARGUMENTS.scenario is None:
        print("Please specify a scenario using '--scenario SCENARIONAME'\n\n")
        PARSER.print_help(sys.stdout)
        sys.exit(0)

    main(ARGUMENTS)
