# Create a new scenario tutorial

This tutorial describes how you can create and run a new scenario using the
ScenarioRunner and the ScenarioManager suite.

Let us call the new scenario _NewScenario_. To create it, there are only few
steps required.

## Creating an empty Python class
Go to the Scenarios folder and create a new Python class with the name
_NewScenario_ in a new Python file (_new_scenario.py_). The class should be
derived from the _BasicScenario_ class. As a result, the class should look as
follows:

   ```
   class NewScenario(BasicScenario):
       """
       Some documentation on NewScenario
       """

       timeout = 60            # Timeout of scenario in seconds
       # some ego vehicle parameters
       # some parameters for the other vehicles

       def __init__(self, world, debug_mode=False):
           """
           Initialize all parameters required for NewScenario
           """

           # Setup vehicles
           self.ego_vehicle = ...
           self.other_vehicles = [...]

           # Call constructor of BasicScenario
           super(NewScenario, self).__init__(
             name="NewScenario",
             town="NameOfCarlaTown", # e.g. Town01
             world=world,
             debug_mode=debug_mode)


       def create_behavior(self):
           """
           Setup the behavior for NewScenario
           """

       def create_test_criteria(self):
           """
           Setup the evaluation criteria for NewScenario
           """
   ```

## Filling the Python class

In the NewScenario class, you have to define the following methods mentioned
in the code example.

### Initialize Method
The initialize method is intended to setup all parameters required
for the scenario and all vehicles. This includes selecting the correct vehicles,
spawning them at the correct location, etc. To simplify this, you may want to
use the _setup_vehicle()_ function defined in basic_scenario.py

### CreateBehavior method
This method should setup the behavior tree that contains the behavior of all
non-ego vehicles during the scenario. The behavior tree should use py_trees and
the atomic behaviors defined in _atomic_scenario_behavior.py_

### CreateTestCriteria method
This method should setup a list with all evaluation criteria for the scenario.
The criteria should be based on the atomic criteria defined in
_atomic_scenario_criteria.py_.

Note: From this list a parallel py_tree will be created automatically!
