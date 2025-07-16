# Gidamart - Real Estate Management System

![Gidamart Logo](src/static/images/hero-house.png)

A comprehensive real estate management system built with Flask, featuring both an admin dashboard for property management and a public-facing website for property browsing and user interaction.

## 🏠 Overview

Gidamart is a modern, responsive real estate website designed specifically for the Nigerian market. It provides a complete solution for real estate agencies to manage their properties, handle customer inquiries, and showcase their listings to potential buyers and renters.

### Key Features

#### 🔧 Admin Dashboard
- **Property Management**: Add, edit, delete, and manage property listings
- **Image Gallery**: Upload multiple images per property with drag-and-drop functionality
- **Inquiry Management**: View and respond to customer inquiries
- **User Applications**: Track and manage property applications
- **Analytics Dashboard**: View statistics and insights
- **Responsive Design**: Works seamlessly on desktop and mobile devices

#### 🌐 Public Website
- **Property Listings**: Browse properties with advanced filtering
- **Image Galleries**: Slideshow galleries with thumbnail navigation
- **User Registration**: Sign up to apply for properties
- **Contact Forms**: Multiple ways to get in touch
- **Responsive Design**: Mobile-first approach
- **SEO Optimized**: Clean URLs and meta tags

#### 🛡️ Security Features
- **User Authentication**: Secure login system with password hashing
- **Admin Protection**: Role-based access control
- **File Upload Security**: Secure image upload with validation
- **CSRF Protection**: Built-in security measures

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gidamart.git
   cd gidamart
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access the application**
   - Public website: http://localhost:5000
   - Admin dashboard: http://localhost:5000/admin/login
   - Default admin credentials:
     - Email: admin@gidamart.com
     - Password: admin123

## 📁 Project Structure

```
gidamart/
├── src/
│   ├── models/
│   │   └── __init__.py          # Database models
│   ├── routes/
│   │   ├── admin.py             # Admin dashboard routes
│   │   ├── public.py            # Public website routes
│   │   └── user.py              # User management routes
│   ├── templates/
│   │   ├── admin/               # Admin dashboard templates
│   │   │   ├── base_admin.html
│   │   │   ├── dashboard.html
│   │   │   ├── login.html
│   │   │   ├── properties.html
│   │   │   ├── property_detail.html
│   │   │   └── inquiries.html
│   │   ├── public/              # Public website templates
│   │   │   ├── base_public.html
│   │   │   ├── home.html
│   │   │   ├── properties.html
│   │   │   ├── property_detail.html
│   │   │   ├── services.html
│   │   │   ├── contact.html
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── base.html            # Base template
│   ├── static/
│   │   ├── css/                 # Custom stylesheets
│   │   ├── js/                  # JavaScript files
│   │   ├── images/              # Static images
│   │   └── uploads/             # User uploaded images
│   ├── database/                # SQLite database files
│   └── main.py                  # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── INSTALLATION.md              # Detailed installation guide
├── API_DOCUMENTATION.md         # API documentation
└── DEPLOYMENT.md                # Deployment guide
```

## 🎨 Features in Detail

### Admin Dashboard

The admin dashboard provides comprehensive tools for managing the real estate business:

**Property Management**
- Add new properties with detailed information
- Upload multiple high-quality images
- Set property status (active/inactive)
- Edit existing property details
- Delete properties with confirmation

**Image Management**
- Drag-and-drop image upload
- Set primary images for listings
- Reorder images
- Delete unwanted images
- Automatic image optimization

**Customer Interaction**
- View all customer inquiries
- Filter inquiries by status
- Respond to inquiries via email
- Track inquiry status (new, read, responded)

**Analytics and Reporting**
- Property statistics
- Inquiry trends
- User application tracking
- Performance metrics

### Public Website

The public-facing website offers an excellent user experience:

**Homepage**
- Hero section with search functionality
- Featured properties showcase
- Company information and statistics
- Call-to-action sections

**Property Listings**
- Grid and list view options
- Advanced filtering (price, location, type)
- Pagination for large datasets
- Property quick preview

**Property Details**
- High-resolution image galleries
- Detailed property information
- Contact agent functionality
- Application submission (for registered users)

**User Features**
- User registration and login
- Property application system
- Inquiry submission
- Newsletter subscription

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing and file uploads
- **SQLite**: Database (easily replaceable with PostgreSQL/MySQL)

### Frontend
- **Bootstrap 5**: CSS framework
- **Bootstrap Icons**: Icon library
- **Vanilla JavaScript**: Interactive functionality
- **Responsive Design**: Mobile-first approach

### Development Tools
- **Python 3.8+**: Programming language
- **pip**: Package management
- **Virtual Environment**: Dependency isolation

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///src/database/app.db
UPLOAD_FOLDER=src/static/uploads
MAX_CONTENT_LENGTH=16777216
DEBUG=True
```

### Database Configuration

The application uses SQLite by default, but can be easily configured for other databases:

```python
# For PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/gidamart'

# For MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:password@localhost/gidamart'
```

## 📱 Responsive Design

Gidamart is built with a mobile-first approach, ensuring excellent user experience across all devices:

- **Desktop**: Full-featured interface with sidebar navigation
- **Tablet**: Optimized layout with collapsible navigation
- **Mobile**: Touch-friendly interface with bottom navigation

## 🔒 Security Features

### Authentication
- Secure password hashing using Werkzeug
- Session-based authentication
- Role-based access control (admin/user)

### File Upload Security
- File type validation
- File size limits
- Secure filename generation
- Upload directory protection

### Data Protection
- SQL injection prevention through ORM
- XSS protection via template escaping
- CSRF protection (can be enhanced with Flask-WTF)

## 🚀 Deployment

### Local Development
```bash
python src/main.py
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 src.main:app
```

#### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "src/main.py"]
```

#### Environment Setup
1. Set `DEBUG=False` in production
2. Use a strong `SECRET_KEY`
3. Configure a production database
4. Set up proper file permissions
5. Use a reverse proxy (nginx)

## 🧪 Testing

### Manual Testing Checklist

**Admin Dashboard:**
- [ ] Admin login functionality
- [ ] Property CRUD operations
- [ ] Image upload and management
- [ ] Inquiry management
- [ ] Dashboard statistics

**Public Website:**
- [ ] Homepage loading and navigation
- [ ] Property listing and filtering
- [ ] Property detail pages
- [ ] User registration and login
- [ ] Contact form submission
- [ ] Responsive design on mobile

### Automated Testing

To add automated tests, create a `tests/` directory:

```python
# tests/test_models.py
import unittest
from src.models import User, Property

class TestModels(unittest.TestCase):
    def test_user_creation(self):
        user = User(email='test@example.com')
        self.assertEqual(user.email, 'test@example.com')
```

## 🤝 Contributing

We welcome contributions to Gidamart! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Ensure responsive design compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/gidamart/issues) page
2. Create a new issue with detailed information
3. Contact the development team

## 🙏 Acknowledgments

- Bootstrap team for the excellent CSS framework
- Flask community for the robust web framework
- Nigerian real estate professionals for domain expertise
- Open source community for inspiration and tools

## 📊 Roadmap

### Version 2.0 (Planned)
- [ ] Advanced search with map integration
- [ ] Property comparison feature
- [ ] Email notifications system
- [ ] Payment integration
- [ ] Multi-language support
- [ ] API for mobile app integration

### Version 3.0 (Future)
- [ ] Machine learning property recommendations
- [ ] Virtual property tours
- [ ] Blockchain property verification
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant support

---

**Built with ❤️ for the Nigerian real estate market**

For more detailed information, please refer to:
- [Installation Guide](INSTALLATION.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT.md)

