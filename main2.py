# main2.py  —  replace your full file with this

from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from database import get_connection
import bcrypt
from datetime import datetime
import os


SERVER_URL = "http://192.168.1.56:8000"

@strawberry.type
class Menu:
    id: int
    name: str
    parentId: int | None
    iconSvg: str | None 
    mobileUrl: str | None
    children: list['Menu']

@strawberry.type
class School:
    id: int
    name: str

@strawberry.type
class Country:
    id: int
    name: str

@strawberry.type
class State:
    id: int
    name: str
    countryId: int

@strawberry.type
class City:
    id: int
    name: str
    stateId: int

@strawberry.type
class AddUserResult:
    id: int

@strawberry.type
class AuthGroup:
    id: int
    name: str

@strawberry.type
class User:
    id: int
    username: str | None
    emailId: str | None
    mobile: str | None
    firstName: str | None
    lastName: str | None
    about: str | None
    profileImage: str | None
    designationId: str | None
    userType: str | None

    presentAddress: str | None
    presentLandmark: str | None
    presentCity: int | None
    presentState: int | None
    presentPincode: str | None

    permanentAddress: str | None
    permanentLandmark: str | None
    permanentCity: int | None
    permanentState: int | None
    permanentPincode: str | None

@strawberry.type
class Ticket:
    id: int
    user_id: int
    title: str
    description: str
    category: str | None
    priority: str | None
    communication_method: str | None
    status: str
    created_at: str
    attachment_name: str | None

@strawberry.type
class AdmissionEnquiry:
    id: int
    student_name: str
    date_of_birth: str
    gender: str
    nationality: str
    current_institution: str | None

    father_name: str
    mother_name: str
    mobile: str
    email: str

    school_id: int
    address: str
    country_id: int
    state_id: int
    city_id: int
    country_name: str | None
    state_name: str | None
    city_name: str | None
    address_pincode: str

    course_applying: str
    academic_year: str
    preferred_campus: str | None
    heard_from: str

    special_requirements: str | None
    questions: str | None
    status_note: str | None

    created_at: str

@strawberry.type
class TicketResult:
    id: int

@strawberry.type
class Query:

    @strawberry.field
    def schools(self) -> list[School]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, school_name
            FROM schools
            ORDER BY school_name
        """)

        rows = cur.fetchall()
        cur.close(); conn.close()

        return [School(id=r[0], name=r[1]) for r in rows]

    @strawberry.field
    def menus(self, groupId: int) -> list[Menu]:
        conn = get_connection()
        cur = conn.cursor()

        if groupId == 1:
            cur.execute("""
                SELECT id, name, parent_id, icon_svg, mobile_url
                FROM auth_menus
                WHERE status = 0 AND show_menu = 0
                ORDER BY priority
            """)
        else:
            cur.execute("""
                SELECT DISTINCT m.id, m.name, m.parent_id, m.icon_svg, m.mobile_url
                FROM auth_menus m
                JOIN auth_groups_permissions gp ON gp.menu_id = m.id
                WHERE gp.group_id = %s
                ORDER BY m.id ASC
            """, (groupId,))

        rows = cur.fetchall()
        cur.close(); conn.close()

        # build tree
        menu_map = {
            r[0]: {
                "id": r[0],
                "name": r[1],
                "parentId": r[2],
                "iconSvg": r[3],
                "mobileUrl": r[4],
                "children": []
            }
            for r in rows
        }
        root = []

        for m in menu_map.values():
            if m["parentId"] and m["parentId"] in menu_map:
                menu_map[m["parentId"]]["children"].append(m)
            else:
                root.append(m)

        def build(m):
            filename = os.path.basename(m["iconSvg"]) if m.get("iconSvg") else None

            icon_url = f"{SERVER_URL}/menu-icons/{filename}" if filename else None

            return Menu(
                id=m["id"],
                name=m["name"],
                parentId=m["parentId"],
                iconSvg=icon_url,
                mobileUrl=m.get("mobileUrl"),
                children=[build(c) for c in m["children"]]
            )

        return [build(m) for m in root]

    @strawberry.field
    def users(self) -> list[User]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id, 
                u.username, 
                u.email_id, 
                u.mobile, 
                u.first_name, 
                u.last_name, 
                u.designation_id,
                u.profile_image,
                ag.name as user_type
            FROM users u
            LEFT JOIN auth_groups ag ON u.user_type_id = ag.id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [    
            User(
                id=r[0],
                username=r[1],
                emailId=r[2],
                mobile=r[3],
                firstName=r[4],
                lastName=r[5],
                designationId=r[6],
                profileImage=f"{SERVER_URL}/{r[7]}" if r[7] else None,
                userType=r[8],

                about=None,

                presentAddress=None,
                presentLandmark=None,
                presentCity=None,
                presentState=None,
                presentPincode=None,

                permanentAddress=None,
                permanentLandmark=None,
                permanentCity=None,
                permanentState=None,
                permanentPincode=None,
            )
            for r in rows
        ]

    @strawberry.field
    def user(self, userId: int) -> User | None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id, u.username, u.email_id, u.mobile,
                u.first_name, u.last_name, u.about, u.profile_image,
                u.present_address, u.present_landmark, u.present_city, u.present_state, u.present_pincode,
                u.permanent_address, u.permanent_landmark, u.permanent_city, u.permanent_state, u.permanent_pincode,
                u.designation_id,
                u.user_type_id
            FROM users u
            WHERE u.id = %s
        """, (userId,))
        r = cur.fetchone()
        cur.close(); conn.close()
        if not r: return None
        return User(
            id=r[0],
            username=r[1],
            emailId=r[2],
            mobile=r[3],
            firstName=r[4],
            lastName=r[5],
            about=r[6],
            profileImage=f"{SERVER_URL}/{r[7]}" if r[7] else None,

            presentAddress=r[8],
            presentLandmark=r[9],
            presentCity=r[10],
            presentState=r[11],
            presentPincode=r[12],

            permanentAddress=r[13],
            permanentLandmark=r[14],
            permanentCity=r[15],
            permanentState=r[16],
            permanentPincode=r[17],

            designationId=r[18],
            userType=str(r[19]) if r[19] else None,  
        )

    @strawberry.field
    def search_users(self, query: str) -> list[User]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email_id, mobile, first_name, last_name, designation_id
            FROM users
            WHERE username ILIKE %s OR email_id ILIKE %s OR mobile LIKE %s
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [
            User(id=r[0], username=r[1], email_id=r[2], mobile=r[3],
                 first_name=r[4], last_name=r[5], designation_id=r[6],
                 about=None, profile_image=None,
                 present_address=None, present_landmark=None, present_city=None,
                 present_state=None, present_pincode=None,
                 permanent_address=None, permanent_landmark=None, permanent_city=None,
                 permanent_state=None, permanent_pincode=None)
            for r in rows
        ]

    @strawberry.field
    def tickets_by_user(self, userId: int) -> list[Ticket]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, title, description, category, priority,
                communication_method, status, created_at, attachment_name
            FROM support_tickets WHERE user_id = %s ORDER BY created_at DESC
        """, (userId,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [Ticket(
            id=r[0], user_id=r[1], title=r[2], description=r[3],
            category=r[4], priority=r[5] if r[5] else "Medium",
            communication_method=r[6], status=r[7],
            created_at=str(r[8]), attachment_name=r[9]
        ) for r in rows]

    @strawberry.field
    def all_tickets(self) -> list[Ticket]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.user_id, u.username,
                t.title, t.description, t.category,
                t.priority, t.communication_method, t.status, t.created_at, t.attachment_name
            FROM support_tickets t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [Ticket(
            id=r[0], user_id=r[1],
            title=f"{r[2]} — {r[3]}",
            description=r[4], category=r[5],
            priority=str(r[6]) if r[6] else "Low",
            communication_method=r[7], status=r[8],
            created_at=r[9].isoformat(), attachment_name=r[10]
        ) for r in rows]
    

    @strawberry.field
    def admission_enquiries(self) -> list[AdmissionEnquiry]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
SELECT 
        ae.id, ae.student_name, ae.date_of_birth, ae.gender, ae.nationality,
        ae.current_institution, ae.father_name, ae.mother_name,
        ae.mobile, ae.email, ae.school_id, ae.address,

        ae.country_id, ae.state_id, ae.city_id, ae.address_pincode,

        c.name as country_name,
        s.name as state_name,
        ci.city as city_name,

        ae.course_applying, ae.academic_year, ae.preferred_campus,
        ae.heard_from, ae.special_requirements, ae.questions,
        ae.status_note, ae.created_at

    FROM admission_enquiries ae
    LEFT JOIN countries c ON ae.country_id = c.id
    LEFT JOIN states s ON ae.state_id = s.id
    LEFT JOIN cities ci ON ae.city_id = ci.id

    ORDER BY ae.created_at DESC
            
        """)

        rows = cur.fetchall()
        cur.close(); conn.close()

        return [
            AdmissionEnquiry(
                id=r[0],
                student_name=r[1],
                date_of_birth=str(r[2]),
                gender=r[3],
                nationality=r[4],
                current_institution=r[5],
                father_name=r[6],
                mother_name=r[7],
                mobile=r[8],
                email=r[9],
                school_id=r[10],
                address=r[11],
                country_id=r[12],
                state_id=r[13],
                city_id=r[14],
                address_pincode=r[15],
                country_name=r[16],
                state_name=r[17],
                city_name=r[18],
                course_applying=r[19],
                academic_year=r[20],
                preferred_campus=r[21],
                heard_from=r[22],
                special_requirements=r[23],
                questions=r[24],
                status_note=r[25],
                created_at=str(r[26]),
            )
            for r in rows
        ]
    
    @strawberry.field
    def countries(self) -> list[Country]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM countries ORDER BY name")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [Country(id=r[0], name=r[1]) for r in rows]


    @strawberry.field
    def states(self, countryId: int) -> list[State]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, country_id FROM states WHERE country_id = %s ORDER BY name",
            (countryId,)
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [State(id=r[0], name=r[1], countryId=r[2]) for r in rows]


    @strawberry.field
    def cities(self, stateId: int) -> list[City]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, city, state_id FROM cities WHERE state_id = %s ORDER BY city",
            (stateId,)
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [City(id=r[0], name=r[1], stateId=r[2]) for r in rows]

    @strawberry.field
    def classes(self) -> list[Country]:  # reuse simple structure
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, class_name FROM m_classes ORDER BY class_number")
        rows = cur.fetchall()
        cur.close(); conn.close()

        return [Country(id=r[0], name=r[1]) for r in rows]

    @strawberry.field
    def admission_enquiry_by_id(self, id: int) -> AdmissionEnquiry | None:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                ae.id, ae.student_name, ae.date_of_birth, ae.gender, ae.nationality,
                ae.current_institution, ae.father_name, ae.mother_name,
                ae.mobile, ae.email, ae.school_id, ae.address,

                ae.country_id, ae.state_id, ae.city_id, ae.address_pincode,

                c.name as country_name,
                s.name as state_name,
                ci.city as city_name,

                ae.course_applying, ae.academic_year, ae.preferred_campus,
                ae.heard_from, ae.special_requirements, ae.questions,
                ae.status_note, ae.created_at

            FROM admission_enquiries ae
            LEFT JOIN countries c ON ae.country_id = c.id
            LEFT JOIN states s ON ae.state_id = s.id
            LEFT JOIN cities ci ON ae.city_id = ci.id

            WHERE ae.id = %s
        """, (id,))

        r = cur.fetchone()
        cur.close(); conn.close()

        if not r:
            return None

        return AdmissionEnquiry(
            id=r[0],
            student_name=r[1],
            date_of_birth=str(r[2]),
            gender=r[3],
            nationality=r[4],
            current_institution=r[5],
            father_name=r[6],
            mother_name=r[7],
            mobile=r[8],
            email=r[9],
            school_id=r[10],
            address=r[11],

            country_id=r[12],
            state_id=r[13],
            city_id=r[14],
            address_pincode=r[15],

            country_name=r[16],
            state_name=r[17],
            city_name=r[18],

            course_applying=r[19],
            academic_year=r[20],
            preferred_campus=r[21],
            heard_from=r[22],
            special_requirements=r[23],
            questions=r[24],
            status_note=r[25],
            created_at=str(r[26]),
        )
    
    @strawberry.field
    def auth_groups(self) -> list[AuthGroup]:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name 
            FROM auth_groups 
            WHERE status = 0
            ORDER BY id
        """)

        rows = cur.fetchall()
        cur.close(); conn.close()

        return [AuthGroup(id=r[0], name=r[1]) for r in rows]


@strawberry.type
class Mutation:

    @strawberry.mutation
    def login(self, email: str, password: str) -> int:
        conn = get_connection()
        cur = conn.cursor()
        now = datetime.utcnow()

        # Look up by email in auth_identities
        cur.execute("""
            SELECT ai.user_id, ai.secret2
            FROM auth_identities ai
            WHERE ai.type = 'email_password' AND ai.secret = %s
        """, (email.strip(),))
        row = cur.fetchone()

        success = 0
        user_id = None

        if row:
            user_id, hashed = row
            # Verify bcrypt hash
            try:
                if bcrypt.checkpw(password.strip().encode('utf-8'), hashed.encode('utf-8')):
                    success = 1
                    # Update last_used_at in auth_identities
                    cur.execute("""
                        UPDATE auth_identities SET last_used_at = %s
                        WHERE type = 'email_password' AND secret = %s
                    """, (now, email.strip()))
            except Exception:
                success = 0

        # Log the attempt in auth_logins
        cur.execute("""
            INSERT INTO auth_logins
            (ip_address, user_agent, id_type, identifier, user_id, date, success)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('0.0.0.0', 'flutter-app', 'email_password', email.strip(),
              user_id if success else None, now, success))

        conn.commit()
        cur.close(); conn.close()

        if not success:
            raise Exception("Invalid Credentials")

        return user_id

    @strawberry.mutation
    def add_user(
        self,
        username: str,
        password: str,
        emailId: str,
        mobile: str | None = None,
        firstName: str | None = None,
        lastName: str | None = None,
        about: str | None = None,
        designationId: str | None = None,
        userTypeId: int | None = None,
        schoolId: int | None = None,

        presentAddress: str | None = None,
        presentLandmark: str | None = None,
        presentCity: int | None = None,
        presentState: int | None = None,
        presentPincode: str | None = None,

        permanentAddress: str | None = None,
        permanentLandmark: str | None = None,
        permanentCity: int | None = None,
        permanentState: int | None = None,
        permanentPincode: str | None = None,
    ) -> AddUserResult:
        conn = get_connection()
        cur = conn.cursor()
        now = datetime.utcnow()

        # Hash the password with bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user — set timestamps, store plain password in paswd (as requested)
        cur.execute("""
            INSERT INTO users (
                username, paswd, email_id, mobile,
                first_name, last_name, about, designation_id, user_type_id, school_id,
                present_address, present_landmark, present_city, present_state, present_pincode,
                permanent_address, permanent_landmark, permanent_city, permanent_state, permanent_pincode,
                created_at, updated_at, active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, 1)
            RETURNING id
        """, (
            username, password, emailId, mobile,
            firstName, lastName, about, designationId, userTypeId, schoolId,
            presentAddress, presentLandmark, presentCity, presentState, presentPincode,
            permanentAddress, permanentLandmark, permanentCity, permanentState, permanentPincode,
            now, now
        ))

        new_id = cur.fetchone()[0]

        # Insert into auth_identities (email + bcrypt hash)
        cur.execute("""
            INSERT INTO auth_identities
            (user_id, type, secret, secret2, created_at, updated_at)
            VALUES (%s, 'email_password', %s, %s, %s, %s)
        """, (new_id, emailId, hashed, now, now))

        conn.commit()
        cur.close(); conn.close()
        return AddUserResult(id=new_id)

    @strawberry.mutation
    def update_user(
        self,
        user_id: int,
        username: str | None = None,
        emailId: str | None = None,
        mobile: str | None = None,
        firstName: str | None = None,
        lastName: str | None = None,
        about: str | None = None,
        designationId: str | None = None,
        presentAddress: str | None = None,
        presentLandmark: str | None = None,
        presentCity: int | None = None,
        presentState: int | None = None,
        presentPincode: str | None = None,
        permanentAddress: str | None = None,
        permanentLandmark: str | None = None,
        permanentCity: int | None = None,
        permanentState: int | None = None,
        permanentPincode: str | None = None,
        profileImage: str | None = None,
        userTypeId: int | None = None,
    ) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET
                username          = COALESCE(%s, username),
                email_id          = COALESCE(%s, email_id),
                mobile            = COALESCE(%s, mobile),
                first_name        = COALESCE(%s, first_name),
                last_name         = COALESCE(%s, last_name),
                about             = COALESCE(%s, about),
                designation_id    = COALESCE(%s, designation_id),
                present_address   = COALESCE(%s, present_address),
                present_landmark  = COALESCE(%s, present_landmark),
                present_city      = COALESCE(%s, present_city),
                present_state     = COALESCE(%s, present_state),
                present_pincode   = COALESCE(%s, present_pincode),
                permanent_address  = COALESCE(%s, permanent_address),
                permanent_landmark = COALESCE(%s, permanent_landmark),
                permanent_city     = COALESCE(%s, permanent_city),
                permanent_state    = COALESCE(%s, permanent_state),
                permanent_pincode  = COALESCE(%s, permanent_pincode),
                profile_image      = COALESCE(%s, profile_image),
                user_type_id      = COALESCE(%s, user_type_id),
                updated_at         = NOW()
            WHERE id = %s
        """, (
    username, emailId, mobile, firstName, lastName, about, designationId,
    presentAddress, presentLandmark, presentCity, presentState, presentPincode,
    permanentAddress, permanentLandmark, permanentCity, permanentState, permanentPincode,
    profileImage, userTypeId, user_id
        ))
        conn.commit()
        cur.close(); conn.close()
        return "User Updated Successfully"

    @strawberry.mutation
    def delete_user(self, user_id: int) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close(); conn.close()
        return "User Deleted"

    @strawberry.mutation
    def create_ticket(self, user_id: int, title: str, description: str,
                    category: str, priority: str,
                    communication_method: str | None = None) -> TicketResult:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO support_tickets
            (user_id, title, description, category, priority, communication_method)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, title, description, category, priority, communication_method))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close(); conn.close()
        return TicketResult(id=new_id)

    @strawberry.mutation
    def update_ticket(self, ticket_id: int, title: str | None = None,
                      description: str | None = None, category: str | None = None,
                      communication_method: str | None = None) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE support_tickets SET
                title                = COALESCE(%s, title),
                description          = COALESCE(%s, description),
                category             = COALESCE(%s, category),
                communication_method = COALESCE(%s, communication_method)
            WHERE id = %s
        """, (title, description, category, communication_method, ticket_id))
        conn.commit()
        cur.close(); conn.close()
        return "Ticket Updated Successfully"

    @strawberry.mutation
    def update_ticket_status(self, ticket_id: int, status: str) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE support_tickets SET status = %s WHERE id = %s", (status, ticket_id))
        conn.commit()
        cur.close(); conn.close()
        return "Status Updated"

    @strawberry.mutation
    def delete_ticket(self, id: int) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM support_tickets WHERE id = %s", (id,))

        result = cur.fetchone()
        if not result:
            cur.close(); conn.close()
            raise Exception("Ticket not found")
        if result[0] != "Open":
            cur.close(); conn.close()
            raise Exception("Only OPEN tickets can be deleted")
        cur.execute("DELETE FROM support_tickets WHERE id = %s", (id,))
        conn.commit()
        cur.close(); conn.close()
        return "Ticket Deleted Successfully"


    @strawberry.mutation
    def create_admission_enquiry(
        self,
        studentName: str,
        dateOfBirth: str,
        gender: str,
        nationality: str,
        currentInstitution: str | None,

        fatherName: str,
        motherName: str,
        mobile: str,
        email: str,

        schoolId: int,
        address: str,
        countryId: int,
        stateId: int,
        cityId: int,
        addressPincode: str,

        courseApplying: str,
        academicYear: str,
        preferredCampus: str | None,
        heardFrom: str,

        specialRequirements: str | None,
        questions: str | None,
    ) -> str:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO admission_enquiries (
                student_name, date_of_birth, gender, nationality,
                current_institution,
                father_name, mother_name, mobile, email,
                school_id, address, country_id, state_id, city_id,
                address_pincode,
                course_applying, academic_year, preferred_campus,
                heard_from, special_requirements, questions
            )
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s,
                    %s, %s, %s,
                    %s, %s, %s)
        """, (
            studentName, dateOfBirth, gender, nationality,
            currentInstitution,
            fatherName, motherName, mobile, email,
            schoolId, address, countryId, stateId, cityId,
            addressPincode,
            courseApplying, academicYear, preferredCampus,
            heardFrom, specialRequirements, questions
        ))

        conn.commit()
        cur.close()
        conn.close()

        return "Enquiry Submitted"  


schema = strawberry.Schema(query=Query, mutation=Mutation)