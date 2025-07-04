import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import datetime

@frappe.whitelist()
def create(booking_name, email, contact_number, package, booking_date, variation_quantity, participants=None, special_requests=None):
	"""
	Create a new booking.
	Args:
		booking_name (str): Name of the booking.
		email (str): Email address.
		contact_number (str): Phone number.
		package (str): Name of the package.
		booking_date (str): Booking date (YYYY-MM-DD).
		variation_quantity (list): List of variation_quantity.
		participants (list): List of participant details (optional).
		special_requests (list): List of special requests (optional).
	Returns: Newly created booking details.
	"""
	try:
		# Validate inputs
		if not all([booking_name, email, contact_number, package, booking_date]):
			raise ValueError("All required fields must be provided")
		
		# Validate package exists
		package = frappe.get_doc("Package", package)
		if not package:
			raise ValueError(f"Package '{package}' not found")
		
		# Validate booking date format and value
		try:
			booking_date = frappe.utils.getdate(booking_date)
		except ValueError:
			raise ValueError("Invalid booking date format. Use YYYY-MM-DD")
		
		if not variation_quantity:
			raise ValueError("Invalid variations provided")
			
		# Validate email format
		if not frappe.utils.validate_email_address(email):
			raise ValueError("Invalid email address")
		
		# Create new booking
		booking = frappe.get_doc({
			"doctype": "Booking",
			"booking_name": booking_name,
			"email": email,
			"contact_number": contact_number,
			"package": package.name,
			"booking_date": booking_date,
			"status": "Created",
			"participants": participants or [],
			"special_requests": special_requests or [],
			"variation_quantity": variation_quantity
		})
		
		booking.insert(ignore_permissions=False)
		frappe.db.commit()
		
		return {
			"status": "success",
			"data": {
				"name": booking.name,
				"booking_name": booking.booking_name,
				"email": booking.email,
				"contact_number": booking.contact_number,
				"package": booking.package,
				"booking_date": booking.booking_date,
				"quantity": booking.quantity,
				"status": booking.status,
				"participants": booking.participants,
				"special_requests": booking.special_requests,
				"variation_quantity": [
					{ "variation": row.variation, "quantity": row.quantity }
					for row in booking.variation_quantity
				]
			},
			"message": "Booking created successfully"
		}
	except Exception as e:
		frappe.db.rollback()
		return {
			"status": "error",
			"message": f"Failed to create booking: {str(e)}",
			"data": {}
		}

@frappe.whitelist()
def finalize(booking_name):
	"""
	Update the status of a booking.
	Args:
		booking_name (str): Name of the booking.
		status (str): New status (Pending, Approved, Rejected).
	Returns: Updated booking details.
	"""
	try:
		booking = frappe.get_doc("Booking", booking_name)
		if not booking:
			raise ValueError(f"Booking '{booking_name}' not found")
		
		if booking.status != "Created":
			raise ValueError(f"Booking '{booking_name}' already finalized")

		# Update status
		booking.status = "Pending"
		booking.save(ignore_permissions=False)
		frappe.db.commit()
		
		return {
			"status": "success",
			"data": {
				"name": booking.name,
				"booking_name": booking.booking_name,
				"status": booking.status
			},
			"message": "Booking status updated successfully"
		}
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": f"Booking '{booking_name}' not found",
			"data": {}
		}
	except Exception as e:
		frappe.db.rollback()
		return {
			"status": "error",
			"message": f"Failed to update booking status: {str(e)}",
			"data": {}
		}
	
@frappe.whitelist()
def update_manifest(booking_name, participants=None):
	try:
		booking = frappe.get_doc("Booking", booking_name)
		if not booking:
			raise ValueError(f"Booking '{booking_name}' not found")
		
		if len(participants) > booking.quantity:
			raise ValueError(f"Manifest has too many participants")

		booking.set('participants', [])
		for p in participants:
			booking.append('participants', {"doctype": "Booking Participant",**p})
		
		booking.save(ignore_permissions=False)
		frappe.db.commit()

		meta = frappe.get_meta("Booking Participant")
		declared_fields = [
			df.fieldname for df in meta.fields
			if df.fieldname and df.fieldtype not in ["Section Break", "Column Break"]
		]
		
		return {
			"status": "success",
			"data": {
				"name": booking.name,
				"booking_name": booking.booking_name,
				"status": booking.status,
				"participants": [
					{field: row.get(field) for field in declared_fields}
					for row in booking.participants
				],
			},
			"message": "Booking status updated successfully"
		}
	
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": f"Booking '{booking_name}' not found",
			"data": {}
		}
	except Exception as e:
		frappe.db.rollback()
		return {
			"status": "error",
			"message": f"Failed to update booking status: {str(e)}",
			"data": {}
		}