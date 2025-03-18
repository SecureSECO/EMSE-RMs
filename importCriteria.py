from criteria import CriteriaStore
# 🔹 Initialize criteria store
store = CriteriaStore()

# 🔥 Load criteria from CSV
store.load_from_csv("csv/Systematic Reviews.csv")
store.print_all_criteria()
# 🔍 Generate a prompt for checking a specific criterion
# research_method = "Controlled Experiment"
# criterion_description = "Controlled Experiment - Randomization is performed"
#
# prompt = store.generate_prompt_for_criterion(research_method, criterion_description)
# print(prompt)