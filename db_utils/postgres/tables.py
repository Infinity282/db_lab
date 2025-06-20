TABLES = {
    "Universities": """
            (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address VARCHAR(255) NOT NULL,
                founded_date DATE NOT NULL
            )
        """,
    "Institutes": """
            (
                id SERIAL PRIMARY KEY,
                university_id INTEGER REFERENCES Universities(id),
                name VARCHAR(255) NOT NULL
            )
        """,
    "Departments": """
            (
                id SERIAL PRIMARY KEY,
                institute_id INTEGER REFERENCES Institutes(id),
                name VARCHAR(255) NOT NULL
            )
        """,
    "Specialties": """
            (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) NOT NULL,
                name VARCHAR(255) NOT NULL
            )
        """,
    "Student_Groups": """
            (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                specialty_id INTEGER REFERENCES Specialties(id),
                name VARCHAR(50) NOT NULL,
                course_year INTEGER
            )
        """,
    "Students": """
            (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                name VARCHAR(255) NOT NULL,
                enrollment_year INTEGER,
                date_of_birth DATE,
                email VARCHAR(255),
                book_number VARCHAR(20)
            )
        """,
    "Course_of_classes": """
            (
                id SERIAL PRIMARY KEY,
                department_id INTEGER REFERENCES Departments(id),
                specialty_id INTEGER REFERENCES Specialties(id),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                tech_requirements TEXT
            )
        """,
    "Class": """
            (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                type VARCHAR(50) NOT NULL
            )
        """,
    "Class_Materials": """
            (
                id SERIAL PRIMARY KEY,
                class_id INTEGER REFERENCES Class(id),
                content TEXT
            )
        """,
    "Schedule": """
            (
                id SERIAL PRIMARY KEY,
                group_id INTEGER REFERENCES Student_Groups(id),
                course_of_class_id INTEGER REFERENCES Course_of_classes(id),
                room VARCHAR(50),
                scheduled_date DATE,
                start_time TIME,
                end_time TIME
            )
        """,
    "Attendance": """
            (
                id SERIAL PRIMARY KEY,
                schedule_id INTEGER REFERENCES Schedule(id),
                student_id INTEGER REFERENCES Students(id),
                attended BOOLEAN NOT NULL,
                absence_reason TEXT
            )
        """
}
