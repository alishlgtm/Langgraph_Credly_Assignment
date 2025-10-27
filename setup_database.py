import sqlite3

def setup_certifications_database():
    """Create and populate the certifications database with your expected data"""
    connection = sqlite3.connect('certifications_data.db')
    cursor = connection.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certifications_data (
            cert_name TEXT NOT NULL,
            points REAL
        )
    ''')
    
    # Insert your expected certification points
    certifications = [
        ('HashiCorp Certified: Terraform Associate', 5.0),
        ('AWS Certified AI Practitioner', 2.5),
        ('AWS Certified Solutions Architect - Professional', 10.0),
        ('AWS Certified Solutions Architect - Associate', 5.0),
        ('AWS Certified Developer - Associate', 5.0),
        ('AWS Certified SysOps Administrator - Associate', 5.0),
        ('AWS Certified DevOps Engineer - Professional', 10.0),
        ('AWS Solution Architect Professional', 10.0),  # Added for your test case
        ('Google Cloud Professional Cloud Architect', 8.0),
        ('Microsoft Certified: Azure Fundamentals',5.0),
        ('Microsoft Certified: Azure Solutions Architect Expert', 8.0),
        ('Certified Kubernetes Administrator (CKA)', 7.0),
        ('CompTIA Security+', 4.5),
        ('Certified Information Systems Security Professional (CISSP)', 9.0),
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO certifications_data VALUES (?, ?)", certifications)
    connection.commit()
    connection.close()
    print(f"✓ Database setup complete - {len(certifications)} certifications added")

if __name__ == "__main__":
    setup_certifications_database()