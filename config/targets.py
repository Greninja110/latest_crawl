"""
Target college websites and their specific URL patterns
"""

# List of target colleges with their base URLs and specific paths
TARGET_COLLEGES = [
    {
        "name": "Indian Institute of Technology Delhi",
        "alias": ["IIT Delhi", "IITD"],
        "base_url": "https://home.iitd.ac.in/",
        "admission_paths": [
            "admissions", 
            "undergraduate-admissions",
            "pg-admissions"
        ],
        "placement_paths": [
            "career", 
            "placement",
            "training-placement"
        ],
        "domain": "iitd.ac.in"
    },
    {
        "name": "Indian Institute of Technology Bombay",
        "alias": ["IIT Bombay", "IITB"],
        "base_url": "https://www.iitb.ac.in/",
        "admission_paths": [
            "en/education/admissions",
            "newacadhome/UGAdmission.jsp",
            "newacadhome/PGAdmission.jsp"
        ],
        "placement_paths": [
            "en/career-and-placement",
            "placement",
            "careers"
        ],
        "domain": "iitb.ac.in"
    },
    {
        "name": "Delhi University",
        "alias": ["DU", "University of Delhi"],
        "base_url": "http://www.du.ac.in/",
        "admission_paths": [
            "admissions",
            "admissions/ug-admissions",
            "admissions/pg-admissions"
        ],
        "placement_paths": [
            "placement-cell",
            "careers",
            "CIC/index.php"
        ],
        "domain": "du.ac.in"
    },
    {
        "name": "Vellore Institute of Technology",
        "alias": ["VIT"],
        "base_url": "https://vit.ac.in/",
        "admission_paths": [
            "admissions",
            "ug",
            "pg"
        ],
        "placement_paths": [
            "placement",
            "campus-placements",
            "careers"
        ],
        "domain": "vit.ac.in"
    },
    {
        "name": "Birla Institute of Technology and Science, Pilani",
        "alias": ["BITS Pilani", "BITS"],
        "base_url": "https://www.bits-pilani.ac.in/",
        "admission_paths": [
            "admissions",
            "bitsat",
            "phd-admissions"
        ],
        "placement_paths": [
            "placement",
            "placements",
            "careers"
        ],
        "domain": "bits-pilani.ac.in"
    },
    # Add your own custom college here as an example
    {
        "name": "mbit",
        "alias": ["My mbit"],
        "base_url": "https://mbit.edu.in",
        "admission_paths": [
            "admissions",
            "apply"
        ],
        "placement_paths": [
            "careers",
            "jobs"
        ],
        "domain": "example.edu"
    }
]

# Custom URL patterns for extracting specific data
CUSTOM_URL_PATTERNS = {
    "admission_patterns": [
        r"admission|apply|enroll|courses",
        r"programs?/[a-z-]+",
        r"undergraduate|graduate|phd",
        r"fee-structure|hostel-fee|scholarships?",
        r"seat|capacity|selection|criteria"
    ],
    "placement_patterns": [
        r"placement|career|recruit|jobs?",
        r"training[-_]and[-_]placement",
        r"campus[-_]placement",
        r"internship|companies|packages?",
        r"salary|alumni"
    ]
}

# Specific keywords to look for in page content
PAGE_CONTENT_INDICATORS = {
    "admission": [
        "admission process", "how to apply", "eligibility criteria",
        "important dates", "application form", "entrance exam",
        "admission schedule", "fee structure", "hostel facility",
        "seat matrix", "reservation policy", "required documents"
    ],
    "placement": [
        "placement record", "placement statistics", "recruiting companies",
        "highest package", "average package", "median salary",
        "placement cell", "internship opportunities", "campus recruitment",
        "placement brochure", "placement report", "recruiting partners"
    ]
}