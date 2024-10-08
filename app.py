import matplotlib
matplotlib.use('Agg')  # Use the non-interactive backend

from flask import Flask, request, render_template
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)

# Load the roles dataset (containing required skills for each role)
roles_dataset_path = './data/roles_dataset.csv'
roles_df = pd.read_csv(roles_dataset_path)

# Proficiency and Importance mappings
proficiency_mapping = {'Beginner': 1, 'Intermediate': 2, 'Expert': 3}
importance_mapping = {'High': 3, 'Medium': 2, 'Low': 1}

def categorize_skills_by_priority(df, user_proficiencies):
    categorized_skills = []
    
    for i, row in df.iterrows():
        skill = row['Skill_Name']
        required_proficiency = row['Skill_Level_Numeric']
        future_importance = row['Future_Skill_Importance_Numeric']
        
        # Get user proficiency (if not provided, assume beginner level)
        user_proficiency = user_proficiencies.get(skill, 1)
        
        # Calculate proficiency gap
        gap = required_proficiency - user_proficiency
        
        # Calculate priority score based on gap and future importance
        priority_score = (gap * future_importance)
        
        # Categorize based on priority score
        if priority_score >= 6:
            priority_category = "High Priority"
        elif 3 <= priority_score < 6:
            priority_category = "Medium Priority"
        else:
            priority_category = "Low Priority"
        
        categorized_skills.append({
            'Skill': skill,
            'Gap': gap,
            'Required Proficiency': required_proficiency,
            'User Proficiency': user_proficiency,
            'Future Importance': row['Future_Skill_Importance'],
            'Priority Category': priority_category,
            'Priority Score': priority_score
        })
    
    return pd.DataFrame(categorized_skills)

def generate_recommendations(categorized_skills_df):
    recommendations = []

    for index, row in categorized_skills_df.iterrows():
        skill = row['Skill']
        gap = row['Gap']
        future_importance = row['Future Importance']
        
        if gap > 0:
            if gap == 1:
                recommendation = f"Small gap for {skill}. Consider additional practice or short courses."
            elif gap == 2:
                recommendation = f"Moderate gap for {skill}. Consider focused training or hands-on projects."
            else:
                recommendation = f"Large gap for {skill}. Consider foundational learning to improve this skill."
        else:
            recommendation = f"You meet the required proficiency for {skill}."
        
        recommendation += f" (Future Importance: {future_importance})."
        
        recommendations.append({
            'Skill': skill,
            'Gap': gap,
            'Future Importance': future_importance,
            'Recommendation': recommendation
        })

    return pd.DataFrame(recommendations)

@app.route('/', methods=['GET', 'POST'])
def home():
    # Extract unique roles from the dataset to dynamically populate the dropdown
    roles_list = roles_df['Role_Name'].unique().tolist()

    if request.method == 'POST':
        # Get the selected role from the form
        role = request.form.get('role')

        # Filter the dataset for the selected role to get the required skills
        role_skills_df = roles_df[roles_df['Role_Name'] == role]

        if role_skills_df.empty:
            error_message = f"The role '{role}' does not exist in the dataset."
            return render_template('form_with_results.html', error_message=error_message, roles=roles_list)

        # Extract the skills related to the selected role
        required_skills = role_skills_df['Skill_Name'].tolist()
        required_proficiencies = role_skills_df['Skill_Level'].map(proficiency_mapping).tolist()
        future_importance = role_skills_df['Future_Skill_Importance'].tolist()

        if 'proficiencies' in request.form:
            # Handle empty proficiency fields: Filter out empty strings and convert valid values to integers
            user_proficiencies = [int(p) if p.isdigit() else 0 for p in request.form.getlist('proficiencies')]

            # Create user proficiency dictionary
            user_skill_proficiency_dict = dict(zip(required_skills, user_proficiencies))
            
            # Categorize skills based on proficiency and future importance
            role_skills_df['Skill_Level_Numeric'] = role_skills_df['Skill_Level'].map(proficiency_mapping)
            role_skills_df['Future_Skill_Importance_Numeric'] = role_skills_df['Future_Skill_Importance'].map(importance_mapping)
            categorized_skills_df = categorize_skills_by_priority(role_skills_df, user_skill_proficiency_dict)
            
            # Generate recommendations based on priority and gaps
            recommendations_df = generate_recommendations(categorized_skills_df)

            # Generate the bar chart for better visualization of skill gaps
            plt.figure(figsize=(10, 6))
            bar_width = 0.35
            index = range(len(required_skills))
            
            # Plot user proficiency vs required proficiency
            plt.bar(index, user_proficiencies, bar_width, label='User Proficiency', color='skyblue')
            plt.bar([i + bar_width for i in index], required_proficiencies, bar_width, label='Required Proficiency', color='orange')

            # Add labels and legend
            plt.xlabel('Skills')
            plt.ylabel('Proficiency Level (1=Beginner, 2=Intermediate, 3=Expert)')
            plt.title(f'Proficiency Gap Analysis for {role}')
            plt.xticks([i + bar_width / 2 for i in index], required_skills, rotation=45, ha='right')
            plt.legend()

            # Save the plot to a string buffer
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            # Close the plot to free up memory
            plt.close()

            # Radar Chart
            labels = np.array(required_skills)
            user_values = np.array(user_proficiencies)
            required_values = np.array(required_proficiencies)

            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            user_values = np.concatenate((user_values, [user_values[0]]))
            required_values = np.concatenate((required_values, [required_values[0]]))
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.fill(angles, required_values, color='orange', alpha=0.25)
            ax.fill(angles, user_values, color='skyblue', alpha=0.6)
            ax.set_yticklabels([])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels)

            img_radar = io.BytesIO()
            plt.savefig(img_radar, format='png')
            img_radar.seek(0)
            plot_url_radar = base64.b64encode(img_radar.getvalue()).decode()
            plt.close()

            # Render the results with the recommendations and visualizations
            return render_template(
                'form_with_results.html',
                plot_url=plot_url,  # Pass the plot URL to the HTML template
                plot_url_radar=plot_url_radar,  # Pass the radar chart
                role=role,
                recommendations=recommendations_df.to_dict(orient='records'),
                roles=roles_list
            )

        # If no proficiencies are submitted yet, just render the form with skills
        return render_template('form_with_results.html', role=role, required_skills=required_skills, roles=roles_list)

    # If it's a GET request, render the form without the skills
    return render_template('form_with_results.html', roles=roles_list)

if __name__ == '__main__':
    app.run(debug=True)
