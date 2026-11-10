import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_theme(style="whitegrid")

# Load data
df = pd.read_excel('D:\\MarketPlace_Agentic_AI\\dist\\84_sites_statistics.xlsx')

# Output directory for images
out_dir = r"C:\Users\adity\.gemini\antigravity-ide\brain\b58132a4-9c0e-4266-88d0-e3ea35b048e6\scratch"
os.makedirs(out_dir, exist_ok=True)

# 1. Distribution of Total Findings
plt.figure(figsize=(10, 6))
sns.histplot(df['Total Findings'], bins=20, kde=True, color='skyblue')
plt.title('Distribution of Total Findings per Site', fontsize=16)
plt.xlabel('Total Findings', fontsize=12)
plt.ylabel('Count of Sites', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'total_findings_dist.png'), dpi=300)
plt.close()

# 2. Findings by Severity (Average per Archetype)
severity_cols = ['Critical', 'High', 'Medium', 'Low']
df_severity_archetype = df.groupby('Archetype')[severity_cols].mean().reset_index()
df_melted = df_severity_archetype.melt(id_vars='Archetype', value_vars=severity_cols, var_name='Severity', value_name='Average Count')

plt.figure(figsize=(12, 7))
sns.barplot(data=df_melted, x='Archetype', y='Average Count', hue='Severity', palette='viridis')
plt.title('Average Findings by Severity per Archetype', fontsize=16)
plt.xlabel('Site Archetype', fontsize=12)
plt.ylabel('Average Number of Findings', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'severity_by_archetype.png'), dpi=300)
plt.close()

# 3. Proportion of Site Archetypes
plt.figure(figsize=(8, 8))
archetype_counts = df['Archetype'].value_counts()
plt.pie(archetype_counts, labels=archetype_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
plt.title('Distribution of Site Archetypes', fontsize=16)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'archetype_pie.png'), dpi=300)
plt.close()

# 4. Boxplot of Total Findings by Archetype
plt.figure(figsize=(12, 7))
sns.boxplot(data=df, x='Archetype', y='Total Findings', palette='Set2')
sns.stripplot(data=df, x='Archetype', y='Total Findings', color=".3", linewidth=0, alpha=0.5)
plt.title('Spread of Total Findings across Archetypes', fontsize=16)
plt.xlabel('Site Archetype', fontsize=12)
plt.ylabel('Total Findings', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'total_findings_by_archetype.png'), dpi=300)
plt.close()

# 5. Meta-eval Passed Status
plt.figure(figsize=(6, 6))
meta_eval_counts = df['Meta-eval Passed'].value_counts()
sns.barplot(x=meta_eval_counts.index, y=meta_eval_counts.values, palette='coolwarm')
plt.title('Meta-eval Passed Status', fontsize=16)
plt.xlabel('Passed', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'meta_eval_status.png'), dpi=300)
plt.close()

print("Visualizations generated successfully.")
