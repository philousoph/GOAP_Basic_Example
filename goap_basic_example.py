"""
Goal-Oriented Action Planning (GOAP) System

This script demonstrates a simplified GOAP system used to build a house.
GOAP is a decision-making architecture that allows entities to achieve a specific goal
by planning sequences of actions. It is based on the A* algorithm and uses heuristics 
to guide the search process.

In this simulation:
- Wood needs to be chopped from the forest.
- Transported wood is limited to a certain capacity (e.g., 3 woods at a time).
- Wood is piled up at the construction site.
- Once enough wood is accumulated, a house is built.

The A* algorithm:
A* is a pathfinding and graph traversal algorithm, which finds the path from a start node
to a target node in the most efficient way possible. It does this by introducing a heuristic,
which estimates the cost from the current node to the target, ensuring the algorithm is
directed in the most promising direction.

Heuristics:
In this GOAP system, the heuristic function computes the difference between the current
state and the goal state, guiding the planner towards states that are more likely to achieve
the goal. Here, we use the sum of absolute differences between the current state and goal state values.
"""

from queue import PriorityQueue

class State:
    """Represents a state of the world. Provides heuristic calculation based on the goal state."""
    
    def __init__(self, state):
        self.state = state

    def __lt__(self, other):
        # Compare states based on the heuristic value
        return self.heuristic() < other.heuristic()

    def heuristic(self):
        # Calculate the heuristic value based on your heuristic function
        goal_state = {"PiledWood": self.state.get("wood_needed_for_house", 5), "HasHouse": 1}

        base_value = sum(abs(self.state.get(key, 0) - goal_state[key]) for key in goal_state)

        # Add a penalty if HandWood is between 1 and transport_capacity - 1
        if 0 < self.state.get("HandWood", 0) < self.state.get("transport_capacity", 0):
            missing_wood = self.state["transport_capacity"] - self.state["HandWood"]
            base_value += 10 * missing_wood  # Increasing the penalty proportionally to missing wood from full capacity

        return base_value



class Action:
    """Base class for all actions. Each action modifies the world's state in some way."""
    
    def __init__(self, name):
        self.name = name

    def is_valid(self, state):
        """Check if the action can be applied in the given state."""
        raise NotImplementedError

    def apply(self, state):
        """Apply the action and get the new state."""
        raise NotImplementedError

# Define specific actions

class ChopWoodAction(Action):
    def __init__(self):
        super().__init__("ChopWood")

    def is_valid(self, state):
        return state.get("ForestWood", 0) > 0 and state.get("HandWood", 0) < state["transport_capacity"]

    def apply(self, state):
        state = state.copy()
        state["HandWood"] = state.get("HandWood", 0) + 1
        state["ForestWood"] = state["ForestWood"] - 1
        return state

    
class TransportWoodAction(Action):
    """Action to transport wood from hand to woodpile."""
    
    def __init__(self):
        super().__init__("TransportWood")

    def is_valid(self, state):
        return (state.get("HandWood", 0) > 0 and 
                state.get("PiledWood", 0) + state.get("HandWood", 0) <= state["wood_needed_for_house"])

    def apply(self, state):
        state = state.copy()
        state["PiledWood"] = state.get("PiledWood", 0) + state["HandWood"]
        state["HandWood"] = 0
        return state



class BuildHouseAction(Action):
    """Action to build a house. Consumes wood from the woodpile."""
    
    def __init__(self):
        super().__init__("BuildHouse")

    def is_valid(self, state):
        return state.get("PiledWood", 0) >= state["wood_needed_for_house"]

    def apply(self, state):
        state = state.copy()
        state["PiledWood"] = state["PiledWood"] - state["wood_needed_for_house"]
        state["HasHouse"] = 1
        return state


class GOAPPlanner:
    """The GOAP Planner. Uses A* algorithm to find the best sequence of actions to achieve the goal."""
    
    def __init__(self, actions):
        """
        Initialize the GOAP planner.

        Parameters:
            actions (list): A list of possible actions that can be taken in the world.

        Attributes:
            actions (list): Stores the provided list of actions for later planning.
        """
        self.actions = actions

    def plan(self, start_state, goal_state):
        """
        Find a plan to reach the goal state from the start state using the A* algorithm.
        
        The function starts with the given start state and explores possible actions
        and their outcomes to reach the goal state in an efficient manner. A heuristic 
        function is used to prioritize which states to explore.

        Parameters:
            start_state (dict): The initial state of the world.
            goal_state (dict): The desired end state of the world.

        Returns:
            list: A list of actions that, when performed sequentially, lead to the goal state. 
                  Returns None if no such plan is found.
        """
        
        # The open_set (PriorityQueue) stores states to be explored along with the plan
        # to reach them. They're sorted based on their heuristic values.
        open_set = PriorityQueue()
        open_set.put((State(start_state), []))
        
        # The closed_set (set) stores states that have already been explored so we don't 
        # revisit them. It uses tuples for hashability.
        closed_set = set()

        # The main loop of the A* algorithm. Continues until there are no states left to explore.
        while not open_set.empty():
            # Get the state with the lowest heuristic value and its associated plan.
            current_state, plan = open_set.get()

            # If the current state meets the goal, return the plan that led to this state.
            if self.is_goal_met(current_state.state, goal_state):
                return plan

            # Add the current state to the closed set to avoid revisiting.
            closed_set.add(tuple(current_state.state.items()))

            # Check all possible actions.
            for action in self.actions:
                # If the action is valid for the current state, compute the result of the action.
                if action.is_valid(current_state.state):
                    new_state = action.apply(current_state.state)
                    # Extend the current plan with the new action.
                    new_plan = plan + [action]

                    # If the new state hasn't been explored yet, add it to the open set.
                    if tuple(new_state.items()) not in closed_set:
                        open_set.put((State(new_state), new_plan))

        # If we've explored all possible states and haven't found a plan, return None.
        return None

    def is_goal_met(self, current_state, goal_state):
        """
        Check if the goal state conditions are met in the current state.
        
        Parameters:
            current_state (dict): The state to check.
            goal_state (dict): The conditions to meet.

        Returns:
            bool: True if all conditions of the goal state are met in the current state, False otherwise.
        """
        for key, value in goal_state.items():
            if current_state.get(key) != value:
                return False
        return True


if __name__ == "__main__":
    initial_state = {
        "ForestWood": 10,
        "HandWood": 0,
        "PileWood": 0,
        "HasHouse": 0,
        "wood_needed_for_house": 5,
        "transport_capacity": 3
    }
    goal_state = {"HasHouse": 1}
    actions = [ChopWoodAction(), TransportWoodAction(), BuildHouseAction()]

    planner = GOAPPlanner(actions)
    plan = planner.plan(initial_state, goal_state)

    if plan:
        print("Plan found:")
        for action in plan:
            print(f"- {action.name}")
        print("House is built!")
    else:
        print("No plan found")
