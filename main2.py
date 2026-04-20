# main2.py  —  replace your full file with this

from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from database import get_connection
import bcrypt
from datetime import datetime

@strawberry.type
class User:
    id: int
    username: str | None
    email_id: str | None
    mobile: str | None
    first_name: str | None
    last_name: str | None
    about: str | None
    profile_image: str | None
    designation_id: str | None = None

    present_address: str | None
    present_landmark: str | None
    present_city: int | None
    present_state: int | None
    present_pincode: str | None

    permanent_address: str | None
    permanent_landmark: str | None
    permanent_city: int | None
    permanent_state: int | None
    permanent_pincode: str | None

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
class TicketResult:
    id: int

@strawberry.type
class Query:

    @strawberry.field
    def users(self) -> list[User]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email_id, mobile, first_name, last_name, designation_id
            FROM users
        """)
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
    def user(self, userId: int) -> User | None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email_id, mobile,
                   first_name, last_name, about, profile_image,
                   present_address, present_landmark, present_city, present_state, present_pincode,
                   permanent_address, permanent_landmark, permanent_city, permanent_state, permanent_pincode,
                   designation_id
            FROM users WHERE id = %s
        """, (userId,))
        r = cur.fetchone()
        cur.close(); conn.close()
        if not r: return None
        return User(
            id=r[0], username=r[1], email_id=r[2], mobile=r[3],
            first_name=r[4], last_name=r[5], about=r[6], profile_image=r[7],
            present_address=r[8], present_landmark=r[9], present_city=r[10],
            present_state=r[11], present_pincode=r[12],
            permanent_address=r[13], permanent_landmark=r[14], permanent_city=r[15],
            permanent_state=r[16], permanent_pincode=r[17],
            designation_id=r[18],
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
    ) -> str:
        conn = get_connection()
        cur = conn.cursor()
        now = datetime.utcnow()

        # Hash the password with bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert user — set timestamps, store plain password in paswd (as requested)
        cur.execute("""
            INSERT INTO users (
                username, paswd, email_id, mobile,
                first_name, last_name, about, designation_id,
                present_address, present_landmark, present_city, present_state, present_pincode,
                permanent_address, permanent_landmark, permanent_city, permanent_state, permanent_pincode,
                created_at, updated_at, active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, 1)
            RETURNING id
        """, (
            username, password, emailId, mobile,
            firstName, lastName, about, designationId,
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
        return "User Added Successfully"

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
                updated_at         = NOW()
            WHERE id = %s
        """, (
            username, emailId, mobile, firstName, lastName, about, designationId,
            presentAddress, presentLandmark, presentCity, presentState, presentPincode,
            permanentAddress, permanentLandmark, permanentCity, permanentState, permanentPincode,
            profileImage, user_id
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


schema = strawberry.Schema(query=Query, mutation=Mutation)