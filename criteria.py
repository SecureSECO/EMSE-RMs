import csv
import os
from collections import defaultdict

class Criterion:
    """Represents a single quality criterion for a research method."""

    def __init__(self, description: str, level: str):
        self.description = description
        self.level = level
        self.attributes = set()  # Stores tuples of (MoSCoW assessment, attribute)

    def add_attribute(self, moscow: str, attribute: str):
        self.attributes.add((moscow, attribute))

    def to_dict(self):
        return {
            "description": self.description,
            "level": self.level,
            "attributes": list(self.attributes)
        }

    def __str__(self):
        return f"Criterion(description={self.description}, level={self.level}, attributes={self.attributes})"


class CriteriaStore:
    """Stores and manages criteria for multiple research methods."""

    def __init__(self):
        self.criteria = defaultdict(set)  # Key: research method, Value: set of Criterion objects

    def load_from_csv(self, file_path: str):
        """Loads criteria from a CSV file using filename as research method."""
        research_method = os.path.splitext(os.path.basename(file_path))[0]

        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header

            for row in reader:
                if len(row) != 4:
                    print(f"Skipping malformed row: {row}")
                    continue

                description, level, moscow, attribute = row
                self.add_criterion(research_method, description, level, moscow, attribute)

    def add_criterion(self, research_method: str, description: str, level: str, moscow: str, attribute: str):
        """Adds a criterion, ensuring descriptions are preserved."""
        existing_criterion = next((c for c in self.criteria[research_method] if c.description == description), None)

        if existing_criterion:
            existing_criterion.add_attribute(moscow, attribute)
        else:
            new_criterion = Criterion(description, level)
            new_criterion.add_attribute(moscow, attribute)
            self.criteria[research_method].add(new_criterion)

    def get_criteria_for_method(self, research_method: str):
        """Retrieves all criteria for a given research method."""
        return [c.to_dict() for c in self.criteria.get(research_method, [])]

    def is_criteria_available(self, research_method: str):
        """
        Checks if a CSV file exists for the given research method in the provided directory.
        If available, loads and returns the full set of criteria.

        :param research_method: The research method to check.
        :param csv_directory: Directory where CSV files are stored.
        :return: List of criteria if found, else None.
        """
        csv_file = os.path.join("csv/", f"{research_method}.csv")
        print(f"{csv_file} is the CSV file")
        if os.path.exists(csv_file):
            print(f"✅ Criteria file found: {csv_file}")
            self.load_from_csv(csv_file)
            return self.get_criteria_for_method(research_method)
        
        print(f"❌ No criteria file found for research method: {research_method}")
        return None
        
    def generate_prompt_for_criterion(self, research_method: str, criterion_description: str):
            """
            Generates a structured prompt for checking whether an article meets a specific criterion.
            """
            criteria_set = self.criteria.get(research_method, [])
            selected_criterion = next((c for c in criteria_set if c.description == criterion_description), None)

            if not selected_criterion:
                return f"No criterion found for {criterion_description} under {research_method}."

            # Group attributes by MoSCoW level
            must_have = [attr for level, attr in selected_criterion.attributes if level.lower() == "must have"]
            other_criteria = [attr for level, attr in selected_criterion.attributes if level.lower() != "must have"]

            # Construct the prompt
            prompt = f"Please check if the article meets the following criterion:\n{criterion_description}\n\n"
            prompt += "It must at least meet the following Must Have criteria:\n"
        
            if must_have:
                prompt += "\n".join(f"- {c}" for c in must_have) + "\n"
            else:
                prompt += "- No explicitly defined 'Must Have' criteria.\n"

            if other_criteria:
                prompt += "\nIf one of these is missing, it can be replaced by at least two of the following:\n"
                prompt += "\n".join(f"- {c}" for c in other_criteria)
                
            prompt += f"\n\nPlease return only the following: Yes or No, depending on the outcome."
            
            return prompt

    def print_all_criteria(self):
        """Prints all research methods and their associated criteria in full detail."""
        for research_method, criteria_set in self.criteria.items():
            print(f"\n🔹 Research Method: {research_method}")
            for criterion in criteria_set:
                print(f"  - Description: {criterion.description}")
                print(f"    Level: {criterion.level}")
                print(f"    Attributes:")
                for moscow, attribute in criterion.attributes:
                    print(f"      - {moscow}: {attribute}")
