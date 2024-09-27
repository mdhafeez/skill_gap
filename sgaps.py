import pandas as pd

# Load the datasets
roles_dataset_path = "./data/roles_dataset.csv"
user_profile_path = "./data/user_profile.csv"

roles_dataset = pd.read_csv(roles_dataset_path)
user_profiles_df = pd.read_csv(user_profile_path)

# Normalize the skill names in the roles dataset for consistency
roles_dataset['Skill Name Normalized'] = roles_dataset['Skill_Name'].str.lower().str.strip()

# Define a dictionary to standardize proficiency levels
proficiency_mapping = {
    'Beginner': 1,
    'Intermediate': 2,
    'Expert': 3
}

# Function to extract individual skills from the "Skill Proficiencies" column in user profiles
def extract_skills_with_proficiency(skill_proficiencies_string):
    skills_with_proficiency = {}
    for skill_proficiency in skill_proficiencies_string.split(', '):
        skill_name, proficiency = skill_proficiency.split('(')
        skills_with_proficiency[skill_name.strip()] = proficiency_mapping[proficiency.strip(')')]
    return skills_with_proficiency

# Normalize the user skills from the user profile dataset for comparison
user_profiles_df['User Skills with Proficiency'] = user_profiles_df['Skill Proficiencies'].apply(extract_skills_with_proficiency)

# Initialize list to store results for CSV export
export_data = []

# Function to categorize skills by priority
def categorize_priority(gap, future_importance):
    if gap >= 2 or future_importance == 'High':
        return 'High Priority'
    elif gap == 1 or future_importance == 'Medium':
        return 'Medium Priority'
    else:
        return 'Low Priority'

# Skill Gap Analysis with Skill Prioritization
def skill_gap_analysis_with_priority(user_id):
    # Filter the user profile by user_id
    user_profile = user_profiles_df[user_profiles_df['User ID'] == user_id].iloc[0]
    
    # Get user's current job role
    user_role = user_profile['Job Role']
    
    # Get the user's current skills and their proficiency levels
    user_skills_with_proficiency = user_profile['User Skills with Proficiency']
    
    # Filter the roles dataset for the user's job role
    role_skills = roles_dataset[roles_dataset['Role_Name'] == user_role]
    
    # Compare the user's skills and proficiencies with the required role skills and proficiencies
    missing_skills = []
    proficiency_gaps = []
    
    for _, row in role_skills.iterrows():
        required_skill = row['Skill Name Normalized']
        required_proficiency = proficiency_mapping[row['Skill_Level']]
        future_importance = row['Future_Skill_Importance']
        
        # Check if the user has the skill and the required proficiency level
        if required_skill not in user_skills_with_proficiency:
            priority = categorize_priority(3, future_importance)  # Max gap assumed for missing skills
            missing_skills.append((required_skill, required_proficiency, priority))
        else:
            user_proficiency = user_skills_with_proficiency[required_skill]
            proficiency_gap = required_proficiency - user_proficiency
            if proficiency_gap > 0:
                priority = categorize_priority(proficiency_gap, future_importance)
                proficiency_gaps.append((required_skill, required_proficiency, user_proficiency, proficiency_gap, priority))
    
    # Prepare messages based on the analysis
    messages = []
    
    # Add missing skills message with priority
    if missing_skills:
        messages.append(f"Missing Skills (with Priority):")
        for skill, proficiency, priority in missing_skills:
            messages.append(f"- {skill} (Required Proficiency: {proficiency}, Priority: {priority})")
    
    # Handle proficiency gaps based on priority
    if proficiency_gaps:
        messages.append(f"\nProficiency Gaps (with Priority):")
        for skill, req_proficiency, user_proficiency, gap, priority in proficiency_gaps:
            if gap == 1:
                messages.append(f"- {skill} (Required: {req_proficiency}, User: {user_proficiency}) - Small gap, Priority: {priority}")
            elif gap == 2:
                messages.append(f"- {skill} (Required: {req_proficiency}, User: {user_proficiency}) - Moderate gap, Priority: {priority}")
            elif gap >= 3:
                messages.append(f"- {skill} (Required: {req_proficiency}, User: {user_proficiency}) - Large gap, Priority: {priority}")
    
    if not missing_skills and not proficiency_gaps:
        messages.append(f"User {user_id} ({user_profile['User Name']}) has all the required skills and proficiencies for the role: {user_role}")
    
    # Join all messages
    result_message = "\n".join(messages)
    
    # Save the result for CSV export
    export_data.append({
        'User ID': user_id,
        'User Name': user_profile['User Name'],
        'Job Role': user_role,
        'Result': result_message
    })
    
    # Output the result
    print(f"User {user_id} ({user_profile['User Name']}) - Job Role: {user_role}")
    print(result_message)
    print("="*50)

# Run skill gap analysis for the first few users and export to CSV
for user_id in range(1, 11):  # Adjust range to analyze more users
    skill_gap_analysis_with_priority(user_id)

# Export the results to a CSV file
export_df = pd.DataFrame(export_data)
export_file_path = "./data/skill_gap_analysis_with_priority.csv"
export_df.to_csv(export_file_path, index=False)

print(f"Skill gap analysis results with priority exported to: {export_file_path}")
