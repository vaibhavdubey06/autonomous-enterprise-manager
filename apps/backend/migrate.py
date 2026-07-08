import os
import glob

def migrate():
    # Directories to search
    search_dirs = ['app/**/*.py', 'tests/**/*.py']
    files_to_migrate = []
    
    for pattern in search_dirs:
        files_to_migrate.extend(glob.glob(f'c:/Users/dubey/autonomous-enterprise-manager/apps/backend/{pattern}', recursive=True))

    for filepath in files_to_migrate:
        if not os.path.isfile(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content
        
        # Replacements
        new_content = new_content.replace('from app.services.llm.llm_service import LLMService', 'from app.services.llm.gateway import LLMGateway')
        
        # We also need to replace LLMService usages with LLMGateway, except in gateway.py and gemini.py which we just created
        if 'gateway.py' in filepath or 'exceptions.py' in filepath or 'models.py' in filepath or 'base.py' in filepath or 'gemini.py' in filepath:
            continue
            
        new_content = new_content.replace('LLMService', 'LLMGateway')
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Migrated: {filepath}')

if __name__ == '__main__':
    migrate()
