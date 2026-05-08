#!/usr/bin/env python3
"""
Neural Mesh Builder - Semantic Repository Network Constructor
استخراج البيانات من جميع المستودعات وتحويلها إلى شبكة عصبية سيمانتية
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Set
from github import Github, GithubException

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# استخراج Token من متغيرات البيئة (GitHub Actions)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ خطأ: متغير GITHUB_TOKEN غير موجود في البيئة")
    sys.exit(1)

# قائمة المفاهيم (Tags) المعروفة وكيفية اكتشافها
CONCEPT_PATTERNS = {
    "AI": {
        "languages": ["Python", "Jupyter Notebook", "JavaScript"],
        "keywords": ["ai", "agent", "machine learning", "ml", "llm", "neural", "genkit", "adk"],
    },
    "Web": {
        "languages": ["JavaScript", "TypeScript", "HTML", "CSS", "React"],
        "keywords": ["web", "frontend", "ui", "react", "nextjs", "vue", "angular", "browser"],
    },
    "Backend": {
        "languages": ["Python", "Go", "Java", "C#", "Rust"],
        "keywords": ["fastapi", "backend", "server", "api", "rest", "grpc", "database"],
    },
    "DevOps": {
        "languages": ["Shell", "Python", "Go", "YAML"],
        "keywords": ["deploy", "docker", "kubernetes", "ci/cd", "github actions", "terraform", "helm"],
    },
    "IoT": {
        "languages": ["C", "C++", "Rust", "Go", "Assembly"],
        "keywords": ["iot", "embedded", "firmware", "microcontroller", "arduino", "sensor"],
    },
    "Data": {
        "languages": ["Python", "SQL", "R", "Scala"],
        "keywords": ["data", "analytics", "database", "sql", "bigquery", "kafka", "redis"],
    },
    "Security": {
        "languages": ["Python", "Go", "C", "Rust"],
        "keywords": ["security", "crypto", "auth", "oauth", "ssl", "tls", "encryption", "audit"],
    },
    "Testing": {
        "languages": ["Python", "JavaScript", "Go", "Java"],
        "keywords": ["test", "testing", "pytest", "jest", "unittest", "coverage", "qa"],
    },
    "Documentation": {
        "languages": ["Markdown", "ReStructuredText", "HTML"],
        "keywords": ["docs", "documentation", "guide", "tutorial", "readme", "manual"],
    },
    "Framework": {
        "languages": ["Python", "JavaScript", "Go", "Java"],
        "keywords": ["framework", "toolkit", "library", "sdk", "gradio", "fastapi"],
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_concepts(repo) -> Set[str]:
    """
    استخراج المفاهيم (Concepts) من معلومات المستودع
    بناءً على لغة البرمجة والكلمات المفتاحية في الوصف والاسم
    """
    concepts = set()
    
    # الحصول على اللغة الأساسية
    repo_language = repo.language or ""
    
    # الحصول على الوصف والاسم
    repo_description = (repo.description or "").lower()
    repo_name = (repo.name or "").lower()
    
    # مزج البيانات للبحث
    combined_text = f"{repo_name} {repo_description}".lower()
    
    # التحقق من كل مفهوم
    for concept, patterns in CONCEPT_PATTERNS.items():
        # التحقق من اللغة
        if repo_language in patterns["languages"]:
            concepts.add(concept)
            continue
        
        # التحقق من الكلمات المفتاحية
        for keyword in patterns["keywords"]:
            if keyword in combined_text:
                concepts.add(concept)
                break
    
    # إذا لم يتم اكتشاف أي مفهوم، أضف "Miscellaneous"
    if not concepts:
        concepts.add("Miscellaneous")
    
    return concepts


def build_neural_mesh(user) -> Dict:
    """
    بناء شبكة عصبية من جميع المستودعات
    """
    print("🔄 جاري جلب المستودعات...")
    
    neural_mesh = {
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "owner": user.login,
            "total_repositories": 0,
        },
        "repositories": {},
        "concept_index": {},  # فهرس عكسي: concept -> list of repos
    }
    
    try:
        # جلب جميع المستودعات
        repos = user.get_repos(type="owner", sort="updated")
        repo_count = 0
        
        for repo in repos:
            repo_count += 1
            print(f"  [{repo_count}] 🔗 معالجة: {repo.name}...", end=" ")
            
            try:
                # استخراج المفاهيم
                concepts = extract_concepts(repo)
                
                # بناء سجل المستودع
                repo_data = {
                    "url": repo.html_url,
                    "description": repo.description or "بدون وصف",
                    "language": repo.language or "Unknown",
                    "concepts": sorted(list(concepts)),
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "is_fork": repo.fork,
                    "topics": repo.topics or [],
                    "last_updated": repo.updated_at.isoformat() if repo.updated_at else None,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                }
                
                # إضافة المستودع للشبكة العصبية
                neural_mesh["repositories"][repo.name] = repo_data
                
                # تحديث فهرس المفاهيم
                for concept in concepts:
                    if concept not in neural_mesh["concept_index"]:
                        neural_mesh["concept_index"][concept] = []
                    neural_mesh["concept_index"][concept].append(repo.name)
                
                print(f"✓ المفاهيم: {', '.join(concepts)}")
                
            except GithubException as e:
                print(f"❌ خطأ: {str(e)}")
                continue
        
        # تحديث العدد الإجمالي
        neural_mesh["metadata"]["total_repositories"] = repo_count
        neural_mesh["metadata"]["unique_concepts"] = len(neural_mesh["concept_index"])
        
        print(f"\n✅ تم معالجة {repo_count} مستودع بنجاح!")
        return neural_mesh
        
    except GithubException as e:
        print(f"❌ خطأ في جلب المستودعات: {str(e)}")
        sys.exit(1)


def save_neural_mesh(neural_mesh: Dict, output_file: str = "urbon_neural_mesh.json"):
    """
    حفظ الشبكة العصبية في ملف JSON
    """
    print(f"\n💾 جاري حفظ النتائج في {output_file}...")
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(neural_mesh, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم حفظ الملف بنجاح!")
        
        # طباعة ملخص
        print("\n" + "="*60)
        print("📊 ملخص الشبكة العصبية:")
        print("="*60)
        print(f"إجمالي المستودعات: {neural_mesh['metadata']['total_repositories']}")
        print(f"المفاهيم الفريدة: {neural_mesh['metadata']['unique_concepts']}")
        print("\n📈 توزيع المفاهيم:")
        for concept, repos in sorted(neural_mesh["concept_index"].items()):
            print(f"  • {concept}: {len(repos)} مستودع")
        print("="*60)
        
    except IOError as e:
        print(f"❌ خطأ في حفظ الملف: {str(e)}")
        sys.exit(1)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n🚀 بدء بناء الشبكة العصبية العصبية...")
    print(f"⏰ الوقت: {datetime.utcnow().isoformat()}")
    print("-" * 60)
    
    try:
        # الاتصال بـ GitHub
        print("🔐 الاتصال بـ GitHub API...")
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        
        print(f"✅ تم الاتصال بنجاح! المستخدم: {user.login}")
        print(f"📊 إجمالي المستودعات: {user.public_repos + user.total_private_repos}")
        print("-" * 60)
        
        # بناء الشبكة العصبية
        neural_mesh = build_neural_mesh(user)
        
        # حفظ النتائج
        save_neural_mesh(neural_mesh)
        
        print("\n✨ اكتملت العملية بنجاح! تم بناء الشبكة العصبية.")
        return 0
        
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
