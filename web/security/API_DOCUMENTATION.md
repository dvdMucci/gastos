# Security API Documentation

## Overview

The Security API provides endpoints for managing whitelisted and blocked IP addresses in the application. This API is built using Django REST Framework and allows administrators to perform CRUD operations on IP security lists.

### Base URL
All API endpoints are prefixed with `/api/security/`

### Authentication
All endpoints require authentication. Users must be logged in and have appropriate permissions to access these endpoints.

### Response Format
All responses are in JSON format. Successful operations return appropriate HTTP status codes and data, while errors return detailed error messages.

---

## Whitelisted IPs Endpoints

These endpoints allow management of IP addresses that are explicitly allowed access to the system.

### List Whitelisted IPs
- **URL**: `/api/security/whitelist/`
- **Method**: `GET`
- **Description**: Retrieve a list of all whitelisted IP addresses
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: None
- **Request Example**:
  ```bash
  GET /api/security/whitelist/
  Authorization: Bearer <token>
  ```
- **Expected Response** (200 OK):
  ```json
  [
    {
      "id": 1,
      "ip": "192.168.1.100",
      "added_by": 1,
      "date_added": "2023-10-07T10:00:00Z",
      "reason": "Trusted internal network"
    }
  ]
  ```

### Create Whitelisted IP
- **URL**: `/api/security/whitelist/`
- **Method**: `POST`
- **Description**: Add a new IP address to the whitelist
- **Authentication**: Required (IsAuthenticated)
- **Required Parameters**:
  - `ip` (string): Valid IP address
- **Optional Parameters**:
  - `reason` (string): Reason for whitelisting
- **Request Example**:
  ```bash
  POST /api/security/whitelist/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "ip": "192.168.1.101",
    "reason": "New trusted device"
  }
  ```
- **Expected Response** (201 Created):
  ```json
  {
    "id": 2,
    "ip": "192.168.1.101",
    "added_by": 1,
    "date_added": "2023-10-07T10:30:00Z",
    "reason": "New trusted device"
  }
  ```

### Retrieve Whitelisted IP
- **URL**: `/api/security/whitelist/{id}/`
- **Method**: `GET`
- **Description**: Get details of a specific whitelisted IP
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: 
  - `id` (integer): Whitelisted IP ID
- **Request Example**:
  ```bash
  GET /api/security/whitelist/1/
  Authorization: Bearer <token>
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "192.168.1.100",
    "added_by": 1,
    "date_added": "2023-10-07T10:00:00Z",
    "reason": "Trusted internal network"
  }
  ```

### Update Whitelisted IP
- **URL**: `/api/security/whitelist/{id}/`
- **Method**: `PUT`
- **Description**: Update all fields of a whitelisted IP
- **Authentication**: Required (IsAuthenticated)
- **Required Parameters**:
  - `ip` (string): Valid IP address
- **Optional Parameters**:
  - `reason` (string): Reason for whitelisting
- **Request Example**:
  ```bash
  PUT /api/security/whitelist/1/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "ip": "192.168.1.100",
    "reason": "Updated reason"
  }
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "192.168.1.100",
    "added_by": 1,
    "date_added": "2023-10-07T10:00:00Z",
    "reason": "Updated reason"
  }
  ```

### Partially Update Whitelisted IP
- **URL**: `/api/security/whitelist/{id}/`
- **Method**: `PATCH`
- **Description**: Update specific fields of a whitelisted IP
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: Any combination of whitelisted IP fields
- **Request Example**:
  ```bash
  PATCH /api/security/whitelist/1/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "reason": "Partially updated reason"
  }
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "192.168.1.100",
    "added_by": 1,
    "date_added": "2023-10-07T10:00:00Z",
    "reason": "Partially updated reason"
  }
  ```

### Delete Whitelisted IP
- **URL**: `/api/security/whitelist/{id}/`
- **Method**: `DELETE`
- **Description**: Remove an IP address from the whitelist
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: 
  - `id` (integer): Whitelisted IP ID
- **Request Example**:
  ```bash
  DELETE /api/security/whitelist/1/
  Authorization: Bearer <token>
  ```
- **Expected Response** (204 No Content): Empty response body

---

## Blocked IPs Endpoints

These endpoints allow management of IP addresses that are blocked due to suspicious activity.

### List Blocked IPs
- **URL**: `/api/security/blocked/`
- **Method**: `GET`
- **Description**: Retrieve a list of all blocked IP addresses
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: None
- **Request Example**:
  ```bash
  GET /api/security/blocked/
  Authorization: Bearer <token>
  ```
- **Expected Response** (200 OK):
  ```json
  [
    {
      "id": 1,
      "ip": "10.0.0.5",
      "reason": "Suspicious login attempts",
      "blocked_at": "2023-10-07T09:00:00Z",
      "blocked_by": 1
    }
  ]
  ```

### Create Blocked IP
- **URL**: `/api/security/blocked/`
- **Method**: `POST`
- **Description**: Add a new IP address to the blocked list
- **Authentication**: Required (IsAuthenticated)
- **Required Parameters**:
  - `ip` (string): Valid IP address
- **Optional Parameters**:
  - `reason` (string): Reason for blocking (defaults to "Actividad sospechosa")
- **Request Example**:
  ```bash
  POST /api/security/blocked/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "ip": "10.0.0.6",
    "reason": "Multiple failed authentication attempts"
  }
  ```
- **Expected Response** (201 Created):
  ```json
  {
    "id": 2,
    "ip": "10.0.0.6",
    "reason": "Multiple failed authentication attempts",
    "blocked_at": "2023-10-07T10:45:00Z",
    "blocked_by": 1
  }
  ```

### Retrieve Blocked IP
- **URL**: `/api/security/blocked/{id}/`
- **Method**: `GET`
- **Description**: Get details of a specific blocked IP
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: 
  - `id` (integer): Blocked IP ID
- **Request Example**:
  ```bash
  GET /api/security/blocked/1/
  Authorization: Bearer <token>
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "10.0.0.5",
    "reason": "Suspicious login attempts",
    "blocked_at": "2023-10-07T09:00:00Z",
    "blocked_by": 1
  }
  ```

### Update Blocked IP
- **URL**: `/api/security/blocked/{id}/`
- **Method**: `PUT`
- **Description**: Update all fields of a blocked IP
- **Authentication**: Required (IsAuthenticated)
- **Required Parameters**:
  - `ip` (string): Valid IP address
- **Optional Parameters**:
  - `reason` (string): Reason for blocking
- **Request Example**:
  ```bash
  PUT /api/security/blocked/1/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "ip": "10.0.0.5",
    "reason": "Updated blocking reason"
  }
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "10.0.0.5",
    "reason": "Updated blocking reason",
    "blocked_at": "2023-10-07T09:00:00Z",
    "blocked_by": 1
  }
  ```

### Partially Update Blocked IP
- **URL**: `/api/security/blocked/{id}/`
- **Method**: `PATCH`
- **Description**: Update specific fields of a blocked IP
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: Any combination of blocked IP fields
- **Request Example**:
  ```bash
  PATCH /api/security/blocked/1/
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "reason": "Partially updated reason"
  }
  ```
- **Expected Response** (200 OK):
  ```json
  {
    "id": 1,
    "ip": "10.0.0.5",
    "reason": "Partially updated reason",
    "blocked_at": "2023-10-07T09:00:00Z",
    "blocked_by": 1
  }
  ```

### Delete Blocked IP
- **URL**: `/api/security/blocked/{id}/`
- **Method**: `DELETE`
- **Description**: Remove an IP address from the blocked list
- **Authentication**: Required (IsAuthenticated)
- **Parameters**: 
  - `id` (integer): Blocked IP ID
- **Request Example**:
  ```bash
  DELETE /api/security/blocked/1/
  Authorization: Bearer <token>
  ```
- **Expected Response** (204 No Content): Empty response body

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request
```json
{
  "ip": ["Enter a valid IP address."],
  "reason": ["This field may not be blank."]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}