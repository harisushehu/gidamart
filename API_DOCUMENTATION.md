# Gidamart API Documentation

This document provides comprehensive information about the Gidamart Real Estate Management System API endpoints, request/response formats, and authentication methods.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Public Endpoints](#public-endpoints)
4. [Admin Endpoints](#admin-endpoints)
5. [User Endpoints](#user-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

## Overview

The Gidamart API is a RESTful web service that provides access to property listings, user management, and administrative functions. The API returns JSON responses and uses standard HTTP status codes.

### Base URL
```
http://localhost:5000
```

### Content Type
All requests and responses use `application/json` content type unless otherwise specified.

### API Versioning
Current API version: v1 (no versioning prefix required)

## Authentication

### Session-Based Authentication
The API uses Flask-Login for session-based authentication. Users must log in through the web interface to access protected endpoints.

### Admin Authentication
Admin endpoints require admin privileges. Users must have `is_admin=True` in their user record.

### Authentication Headers
No special headers required for session-based authentication. The session cookie is automatically handled by the browser.

## Public Endpoints

### Home Page
**GET** `/`

Returns the main homepage with featured properties and company information.

**Response:**
- **200 OK**: HTML page
- **500 Internal Server Error**: Server error

---

### Property Listings
**GET** `/properties`

Retrieves a paginated list of active properties.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 10, max: 50)
- `property_type` (string, optional): Filter by type ('sale' or 'rent')
- `location` (string, optional): Filter by location
- `min_price` (float, optional): Minimum price filter
- `max_price` (float, optional): Maximum price filter

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "title": "Luxury Villa in Damaturu",
      "description": "Beautiful 4-bedroom villa...",
      "price": 25000000,
      "property_type": "sale",
      "location": "Damaturu, Yobe State",
      "bedrooms": 4,
      "bathrooms": 3,
      "area_sqft": 2500,
      "status": "active",
      "created_at": "2024-01-15T10:30:00",
      "images": [
        {
          "id": 1,
          "image_filename": "villa_001.jpg",
          "is_primary": true
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Property Detail
**GET** `/properties/<int:property_id>`

Retrieves detailed information about a specific property.

**Parameters:**
- `property_id` (integer): Property ID

**Response:**
```json
{
  "id": 1,
  "title": "Luxury Villa in Damaturu",
  "description": "Beautiful 4-bedroom villa with modern amenities...",
  "price": 25000000,
  "property_type": "sale",
  "location": "Damaturu, Yobe State",
  "bedrooms": 4,
  "bathrooms": 3,
  "area_sqft": 2500,
  "status": "active",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "images": [
    {
      "id": 1,
      "image_filename": "villa_001.jpg",
      "is_primary": true,
      "upload_order": 0
    },
    {
      "id": 2,
      "image_filename": "villa_002.jpg",
      "is_primary": false,
      "upload_order": 1
    }
  ],
  "related_properties": [
    {
      "id": 2,
      "title": "Modern Apartment",
      "price": 15000000,
      "location": "Potiskum, Yobe State"
    }
  ]
}
```

**Status Codes:**
- **200 OK**: Property found
- **404 Not Found**: Property not found

---

### Contact Form Submission
**POST** `/contact`

Submits a contact inquiry.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+2341234567890",
  "property_id": 1,
  "subject": "buying",
  "message": "I'm interested in this property..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Your inquiry has been submitted successfully. We'll get back to you soon."
}
```

**Status Codes:**
- **200 OK**: Inquiry submitted successfully
- **400 Bad Request**: Invalid input data
- **500 Internal Server Error**: Server error

---

### User Registration
**POST** `/register`

Registers a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "confirm_password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account created successfully. You can now log in.",
  "user_id": 123
}
```

**Status Codes:**
- **201 Created**: User registered successfully
- **400 Bad Request**: Invalid input or email already exists
- **500 Internal Server Error**: Server error

---

### User Login
**POST** `/login`

Authenticates a user and creates a session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "is_admin": false
  }
}
```

**Status Codes:**
- **200 OK**: Login successful
- **401 Unauthorized**: Invalid credentials
- **400 Bad Request**: Invalid input data

---

### Services Page
**GET** `/services`

Returns the services page with information about offered services.

**Response:**
- **200 OK**: HTML page

---

### Contact Page
**GET** `/contact`

Returns the contact page with contact information and form.

**Response:**
- **200 OK**: HTML page

## Admin Endpoints

All admin endpoints require authentication and admin privileges.

### Admin Dashboard
**GET** `/admin/dashboard`

Returns the admin dashboard with statistics and overview.

**Response:**
```json
{
  "statistics": {
    "total_properties": 25,
    "active_properties": 23,
    "total_inquiries": 45,
    "new_inquiries": 8,
    "total_applications": 12,
    "pending_applications": 5
  },
  "recent_properties": [
    {
      "id": 1,
      "title": "Luxury Villa",
      "created_at": "2024-01-15T10:30:00",
      "status": "active"
    }
  ],
  "recent_inquiries": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-15T14:30:00",
      "status": "new"
    }
  ]
}
```

---

### Property Management
**GET** `/admin/properties`

Retrieves all properties for admin management.

**Query Parameters:**
- `page` (integer, optional): Page number
- `status` (string, optional): Filter by status ('active', 'inactive')
- `search` (string, optional): Search in title and description

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "title": "Luxury Villa in Damaturu",
      "price": 25000000,
      "property_type": "sale",
      "location": "Damaturu, Yobe State",
      "status": "active",
      "created_at": "2024-01-15T10:30:00",
      "images_count": 5,
      "inquiries_count": 3,
      "applications_count": 1
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 25,
    "pages": 2
  }
}
```

---

### Add Property
**POST** `/admin/properties`

Creates a new property listing.

**Request Body:**
```json
{
  "title": "Modern Apartment in Potiskum",
  "description": "Beautiful 2-bedroom apartment with modern amenities...",
  "price": 15000000,
  "property_type": "sale",
  "location": "Potiskum, Yobe State",
  "bedrooms": 2,
  "bathrooms": 2,
  "area_sqft": 1200,
  "status": "active"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Property created successfully",
  "property": {
    "id": 26,
    "title": "Modern Apartment in Potiskum",
    "created_at": "2024-01-15T16:30:00"
  }
}
```

**Status Codes:**
- **201 Created**: Property created successfully
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Not authenticated
- **403 Forbidden**: Not admin

---

### Update Property
**PUT** `/admin/properties/<int:property_id>`

Updates an existing property.

**Parameters:**
- `property_id` (integer): Property ID

**Request Body:**
```json
{
  "title": "Updated Property Title",
  "price": 20000000,
  "status": "inactive"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Property updated successfully",
  "property": {
    "id": 1,
    "title": "Updated Property Title",
    "updated_at": "2024-01-15T17:30:00"
  }
}
```

---

### Delete Property
**DELETE** `/admin/properties/<int:property_id>`

Deletes a property and all associated images.

**Parameters:**
- `property_id` (integer): Property ID

**Response:**
```json
{
  "success": true,
  "message": "Property deleted successfully"
}
```

**Status Codes:**
- **200 OK**: Property deleted successfully
- **404 Not Found**: Property not found
- **401 Unauthorized**: Not authenticated
- **403 Forbidden**: Not admin

---

### Upload Property Images
**POST** `/admin/properties/<int:property_id>/images`

Uploads images for a property.

**Parameters:**
- `property_id` (integer): Property ID

**Request Body:**
- Content-Type: `multipart/form-data`
- Field: `images` (multiple files)

**Response:**
```json
{
  "success": true,
  "message": "3 images uploaded successfully",
  "images": [
    {
      "id": 10,
      "image_filename": "abc123.jpg",
      "is_primary": true,
      "upload_order": 0
    },
    {
      "id": 11,
      "image_filename": "def456.jpg",
      "is_primary": false,
      "upload_order": 1
    }
  ]
}
```

**Status Codes:**
- **200 OK**: Images uploaded successfully
- **400 Bad Request**: No images provided or invalid file type
- **404 Not Found**: Property not found
- **413 Payload Too Large**: File size exceeds limit

---

### Delete Property Image
**DELETE** `/admin/images/<int:image_id>`

Deletes a specific property image.

**Parameters:**
- `image_id` (integer): Image ID

**Response:**
```json
{
  "success": true,
  "message": "Image deleted successfully"
}
```

---

### Set Primary Image
**PUT** `/admin/images/<int:image_id>/primary`

Sets an image as the primary image for a property.

**Parameters:**
- `image_id` (integer): Image ID

**Response:**
```json
{
  "success": true,
  "message": "Primary image updated successfully"
}
```

---

### Inquiry Management
**GET** `/admin/inquiries`

Retrieves all contact inquiries.

**Query Parameters:**
- `page` (integer, optional): Page number
- `status` (string, optional): Filter by status ('new', 'read', 'responded')
- `property_id` (integer, optional): Filter by property

**Response:**
```json
{
  "inquiries": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+2341234567890",
      "property_id": 1,
      "property_title": "Luxury Villa in Damaturu",
      "message": "I'm interested in this property...",
      "status": "new",
      "created_at": "2024-01-15T14:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

---

### Update Inquiry Status
**PUT** `/admin/inquiries/<int:inquiry_id>/status`

Updates the status of an inquiry.

**Parameters:**
- `inquiry_id` (integer): Inquiry ID

**Request Body:**
```json
{
  "status": "responded"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Inquiry status updated successfully"
}
```

## User Endpoints

### Apply for Property
**POST** `/properties/<int:property_id>/apply`

Submits an application for a property (requires user authentication).

**Parameters:**
- `property_id` (integer): Property ID

**Request Body:**
```json
{
  "message": "I would like to apply for this property because..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Application submitted successfully",
  "application_id": 15
}
```

**Status Codes:**
- **201 Created**: Application submitted successfully
- **400 Bad Request**: Already applied or invalid data
- **401 Unauthorized**: Not authenticated
- **404 Not Found**: Property not found

---

### User Applications
**GET** `/user/applications`

Retrieves the current user's property applications.

**Response:**
```json
{
  "applications": [
    {
      "id": 15,
      "property_id": 1,
      "property_title": "Luxury Villa in Damaturu",
      "message": "I would like to apply...",
      "status": "pending",
      "created_at": "2024-01-15T16:30:00"
    }
  ]
}
```

---

### Logout
**POST** `/logout`

Logs out the current user and destroys the session.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Error Handling

### Error Response Format
All API errors return a consistent JSON format:

```json
{
  "error": true,
  "message": "Error description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 413 | Payload Too Large - File size exceeds limit |
| 422 | Unprocessable Entity - Validation errors |
| 500 | Internal Server Error - Server error |

### Common Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Input validation failed |
| AUTHENTICATION_REQUIRED | User must be logged in |
| ADMIN_REQUIRED | Admin privileges required |
| RESOURCE_NOT_FOUND | Requested resource not found |
| DUPLICATE_EMAIL | Email already registered |
| INVALID_CREDENTIALS | Login credentials invalid |
| FILE_TOO_LARGE | Uploaded file exceeds size limit |
| INVALID_FILE_TYPE | File type not allowed |

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting to prevent abuse.

### Recommended Limits
- Public endpoints: 100 requests per minute per IP
- Authenticated endpoints: 1000 requests per minute per user
- File upload endpoints: 10 requests per minute per user

## Examples

### JavaScript/Fetch Examples

#### Get Property Listings
```javascript
fetch('/properties?page=1&property_type=sale')
  .then(response => response.json())
  .then(data => {
    console.log('Properties:', data.properties);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

#### Submit Contact Form
```javascript
const contactData = {
  name: 'John Doe',
  email: 'john@example.com',
  message: 'I am interested in your properties'
};

fetch('/contact', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(contactData)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    alert('Message sent successfully!');
  }
});
```

#### Upload Property Images (Admin)
```javascript
const formData = new FormData();
const fileInput = document.getElementById('images');

for (let i = 0; i < fileInput.files.length; i++) {
  formData.append('images', fileInput.files[i]);
}

fetch('/admin/properties/1/images', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Images uploaded:', data.images);
  }
});
```

### Python/Requests Examples

#### Get Property Detail
```python
import requests

response = requests.get('http://localhost:5000/properties/1')
if response.status_code == 200:
    property_data = response.json()
    print(f"Property: {property_data['title']}")
else:
    print(f"Error: {response.status_code}")
```

#### Admin Login and Add Property
```python
import requests

# Login
session = requests.Session()
login_data = {
    'email': 'admin@gidamart.com',
    'password': 'admin123'
}

login_response = session.post('http://localhost:5000/admin/login', json=login_data)

if login_response.status_code == 200:
    # Add property
    property_data = {
        'title': 'New Property',
        'description': 'A beautiful property',
        'price': 10000000,
        'property_type': 'sale',
        'location': 'Lagos, Nigeria',
        'bedrooms': 3,
        'bathrooms': 2,
        'area_sqft': 1500
    }
    
    response = session.post('http://localhost:5000/admin/properties', json=property_data)
    if response.status_code == 201:
        print('Property created successfully')
```

### cURL Examples

#### Get Properties
```bash
curl -X GET "http://localhost:5000/properties?page=1&property_type=sale"
```

#### Submit Contact Form
```bash
curl -X POST "http://localhost:5000/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "message": "I am interested in your properties"
  }'
```

#### Upload Images (with authentication)
```bash
curl -X POST "http://localhost:5000/admin/properties/1/images" \
  -H "Cookie: session=your-session-cookie" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg"
```

## API Testing

### Using Postman
1. Import the API endpoints into Postman
2. Set up environment variables for base URL
3. Create authentication requests for admin endpoints
4. Test all endpoints with various scenarios

### Using pytest
```python
import pytest
import requests

BASE_URL = 'http://localhost:5000'

def test_get_properties():
    response = requests.get(f'{BASE_URL}/properties')
    assert response.status_code == 200
    data = response.json()
    assert 'properties' in data
    assert 'pagination' in data

def test_property_detail():
    response = requests.get(f'{BASE_URL}/properties/1')
    assert response.status_code in [200, 404]
```

## Changelog

### Version 1.0.0
- Initial API implementation
- Property management endpoints
- User authentication
- Image upload functionality
- Contact form submission

### Future Versions
- API versioning
- Rate limiting
- Enhanced search capabilities
- Webhook support
- Mobile app API endpoints

---

For additional support or questions about the API, please refer to the main documentation or create an issue on GitHub.

