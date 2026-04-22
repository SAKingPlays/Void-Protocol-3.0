# VOID PROTOCOL CTF Platform

A comprehensive Capture The Flag (CTF) platform designed for learning and practicing web security vulnerabilities, including IDOR (Insecure Direct Object Reference), cookie manipulation, and hybrid exploitation techniques.

## Features

- **20 Interactive Challenges** across multiple vulnerability categories
- **User Authentication System** with registration, login, and session management
- **Real-time Scoreboard** with live updates
- **User Profiles** tracking solved challenges and submission history
- **Admin Dashboard** for user management and platform oversight
- **Professional Dark Theme** with clean, minimal UI design
- **Responsive Design** for desktop and mobile devices

## Challenge Categories

### IDOR (Insecure Direct Object Reference)
- Internal Ticket System
- Employee Payroll Portal
- Cloud Storage Viewer
- API Profile Viewer
- Order Management System
- Project Collaboration Workspace
- Medical Records Portal
- Invoice Management API
- Private Messaging System
- Task Management Board

### Cookie-Based Vulnerabilities
- Role-Based Cookie Manipulation
- Base64 Encoded Session Cookie
- Cookie Integrity Flaw
- JWT Misconfiguration
- Hidden Cookie Behavior
- Multi-Field Cookie Manipulation
- Signed Cookie (Weak Validation)
- Time-Based Cookie Access

### Hybrid Challenges
- Admin Panel Breach (combines IDOR + Cookie manipulation)

### Web Security
- Authentication & Enumeration

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download the repository**

2. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-login werkzeug
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the platform**
   - Open your browser and navigate to: `http://localhost:5000`

## Default Admin Account

- **Username:** `GuildMaster`
- **Password:** `arcaneallure333666404*`
- **Email:** `admin@voidprotocol.ctf`

⚠️ **Important:** Change the default admin password and `SECRET_KEY` in `app.py` before deploying to production.

## Usage

### For Players

1. **Register an account** on the landing page
2. **Browse challenges** from the dashboard
3. **Solve challenges** by exploiting the vulnerabilities
4. **Submit flags** to earn points
5. **Track progress** on the scoreboard and profile

### For Administrators

1. **Login** with admin credentials
2. **Access the admin dashboard** from the navigation menu
3. **Manage users** - ban/unban accounts
4. **Reset scores** if needed
5. **Monitor platform activity**

## Technology Stack

- **Backend:** Flask (Python web framework)
- **Database:** SQLite (via SQLAlchemy ORM)
- **Authentication:** Flask-Login
- **Password Hashing:** Werkzeug security
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Custom CSS with CSS variables for theming

## Project Structure

```
.
├── app.py                      # Main Flask application
├── instance/
│   └── ctf.db                  # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css           # Main stylesheet
│   └── js/
│       └── main.js             # Frontend JavaScript
├── templates/
│   ├── base.html               # Base template
│   ├── dashboard.html          # User dashboard
│   ├── challenges.html         # Challenge listing
│   ├── view_challenge.html     # Single challenge view
│   ├── scoreboard.html         # Live scoreboard
│   ├── profile.html            # User profile
│   ├── admin.html              # Admin dashboard
│   └── landing.html            # Login/registration page
├── challenge-*.html            # Individual challenge interfaces
└── README.md                   # This file
```

## Security Notes

### Development Environment
This platform is designed for educational purposes and intentionally contains security vulnerabilities. **Do not deploy to production without proper security hardening.**

### Production Deployment Considerations

1. **Change the SECRET_KEY** in `app.py` to a strong, randomly generated value
2. **Change default admin password** immediately
3. **Use a production-grade database** (PostgreSQL, MySQL) instead of SQLite
4. **Enable HTTPS** with SSL/TLS certificates
5. **Implement rate limiting** to prevent brute force attacks
6. **Add CSRF protection** for form submissions
7. **Implement proper input validation** and sanitization
8. **Use environment variables** for sensitive configuration
9. **Set up logging and monitoring**
10. **Regular security audits** and dependency updates

## Challenge Walkthrough

For complete step-by-step solutions to all challenges, refer to `CHALLENGE_WALKTHROUGH_GUIDE.md`.

## API Endpoints

### Public Endpoints
- `GET /` - Landing page (login/registration)
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Authenticated Endpoints
- `GET /dashboard` - User dashboard
- `GET /challenges` - Challenge listing
- `GET /challenge/<id>` - View specific challenge
- `GET /challenge-file/<path>` - Access challenge files
- `POST /submit-flag` - Submit challenge flag
- `GET /scoreboard` - Scoreboard page
- `GET /api/scoreboard` - Scoreboard API (JSON)
- `GET /profile` - User profile

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `POST /admin/users/<id>/ban` - Ban/unban user
- `POST /admin/users/<id>/reset-score` - Reset user score

### Challenge API Endpoints
- `GET /api/tickets?user_id=` - IDOR: Ticket system
- `GET /api/payroll/view?emp_id=` - IDOR: Payroll portal
- `GET /api/files/view?file_id=` - IDOR: Cloud storage
- `GET /api/user/<profile_id>` - IDOR: API profile
- `GET /api/orders/<order_id>` - IDOR: Order management
- `GET /api/projects?team_id=` - IDOR: Project workspace
- `GET /records/view?record_id=` - IDOR: Medical records
- `GET /api/invoices/<invoice_number>` - IDOR: Invoice management
- `GET /messages/thread/<thread_id>` - IDOR: Messaging system
- `GET /api/tasks?project=` - IDOR: Task management
- `GET /challenge/cookie-role` - Cookie: Role manipulation
- `GET /challenge/cookie-base64` - Cookie: Base64 encoding
- `GET /challenge/cookie-integrity` - Cookie: Integrity flaw
- `GET /challenge/cookie-jwt` - Cookie: JWT misconfiguration
- `GET /challenge/cookie-hidden` - Cookie: Hidden behavior
- `GET /challenge/cookie-multi-field` - Cookie: Multi-field manipulation
- `GET /challenge/cookie-signed` - Cookie: Weak signature
- `GET /challenge/cookie-time-based` - Cookie: Time-based access
- `GET /challenge/hybrid/admin-panel` - Hybrid: Admin panel breach

## Customization

### Adding New Challenges

1. **Define the challenge** in `app.py` within the `initialize_challenges()` function
2. **Create the challenge HTML file** in the root directory
3. **Add the API route** in `app.py` if needed
4. **Initialize sample data** in the appropriate initialization function

### Modifying the Theme

Edit `static/css/style.css` to customize colors, fonts, and styling. The theme uses CSS variables defined at the top of the file:

```css
:root {
    --bg-dark: #0d0d0d;
    --bg-darker: #080808;
    --accent-blue: #3b82f6;
    --accent-cyan: #06b6d4;
    --accent-green: #10b981;
    /* ... more variables */
}
```

## Troubleshooting

### Database Issues
If you encounter database errors, delete `instance/ctf.db` and restart the application. The database will be automatically recreated.

### Port Already in Use
If port 5000 is already in use, modify the port in `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change to desired port
```

### Challenge Files Not Loading
Ensure challenge HTML files are in the root directory and the `file_path` in `app.py` matches the actual filename.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided for educational purposes. Use responsibly and ethically.

## Acknowledgments

- Designed for web security education
- Inspired by common CTF challenge formats
- Built with Flask and modern web technologies

## Support

For issues, questions, or suggestions, please open an issue in the repository or contact the maintainers.

---

**Happy Hacking! 🎯**
