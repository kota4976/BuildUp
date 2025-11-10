"""Seed initial skills data"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.skill import Skill


def seed_skills():
    """Seed initial skills"""
    db = SessionLocal()
    
    skills = [
        # Programming Languages
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "PHP", "Ruby", "Swift", "Kotlin", "Dart", "Scala",
        
        # Frontend
        "React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js",
        "HTML", "CSS", "Sass", "Tailwind CSS", "Bootstrap",
        
        # Backend
        "FastAPI", "Django", "Flask", "Express.js", "NestJS", "Spring Boot",
        "Ruby on Rails", "Laravel", "ASP.NET",
        
        # Database
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Firebase", "Supabase",
        
        # DevOps & Cloud
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
        "CI/CD", "GitHub Actions", "Jenkins", "GitLab CI",
        
        # Mobile
        "React Native", "Flutter", "iOS", "Android",
        
        # Data & AI
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "Data Science", "Pandas", "NumPy", "Scikit-learn",
        
        # Tools & Others
        "Git", "Linux", "Nginx", "GraphQL", "REST API", "WebSocket",
        "Microservices", "Agile", "Scrum", "Test-Driven Development"
    ]
    
    try:
        # Check if skills already exist
        existing_count = db.query(Skill).count()
        if existing_count > 0:
            print(f"Skills already exist ({existing_count} skills found). Skipping seed.")
            return
        
        # Add skills
        for skill_name in skills:
            skill = Skill(name=skill_name)
            db.add(skill)
        
        db.commit()
        print(f"Successfully seeded {len(skills)} skills")
        
    except Exception as e:
        print(f"Error seeding skills: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_skills()

