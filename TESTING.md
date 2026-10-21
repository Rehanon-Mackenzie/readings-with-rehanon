### Bugs found by automated testing
| Test | What it caught | Fix |
| --- | --- | --- |
| `test_anonymous_user_sees_login_and_register_links` | The "Log in" link in the My Account dropdown had no text, so logged-out user saw a blank menu item. | Added the missing link text in `base.html`.|
| `test_admin_can_edit_a_reading`, `test_detail_page_shows_the_reading` | `super().save()` was indented inside the `if not self.slug:` block, so readings were only saved the first time. Edits silently did nothing. | Moved `super().save()` out of the `if` block so every save works. |
`FieldError: Unknown field(s) (birth-date)` when running tests | A field name had a hyphen in the form's `fields` list. This does not working with Python naming. | Used VS Code's global search for every instance of `birth-date` and changed each to `birth_date`. |
| `test_booked_slot_rejected` failed: the booking form accepted a slot that was already booked | The form's slot didn't exclude slots, so a client could have booked a slot that was already taken. | Filtered the slot dropdown to free, future slots only: `AvailabilitySlot.objectsfilter(is_booked=False, start_time__gt=timezone.now())`. |
| `test_slot_cannot_have_two_active_bookings` failed: the database allowed two active bookings on the same slot | The `UniqueConstraint` condition was written as Q(status='cancelled') instead of `~Q(status='cancelled')`. Without the `~` (NOT), the rule only applied to cancelled bookings. | Added the `~`. The test still failed, because the migration kept the old rule: the learning was that tests build their database from the migrations not the `models.py`. Therefore, I rolled back, deleted and unapplied the migration and ran `makemigrations` and `migrate` again. All tests passed. |
| `TemplatedDoesNotExist: bookings/book_readings.html` | Typo in the template name in the view. | Corrected it to `bookings/book_reading.html`. |
| `test_successful_payment_confirms_booking` failed: "No templates used to render the response" | Two mistakes in the test, not the view: the fake payment's status was misspelt, `suceeded`, and te line giving the mock return it's value (`mock_retrieve.return_value = self.fake_intent()`) was missed out. The view correctly treated the fake payment as unpaid. | Corrected the spelling and added the missing line. | 


## Manual Testing

### Readings Page Testing

| Feature | Test| Expected | Result  | 
| --------| --- | -------- | ------- |
| Hidden readings | Hide a reading and then view the page as a superuser and a client | Superuser sees the reading with the label "Hidden from clients on it" and client doesn't see the reading | Pass |
| Add reading (client) | Log in as a client and visit `/readings/add/` | Redirected home with "Sorry only the site owner can do that." | Pass |
| Add reading (logged out) | Log out and visit `/readings/add` | Redirected to the login page | Pass |
| Edit reading (client) | Log in as a client and visit `/readings/birth-chart/edit/` | Redirected home with "Sorry only the site owner can do that." | Pass |
| Edit reading (logged out) | Log out and visit `/readings/birth-chart/edit` | Redirected to the login page | Pass |
| Delete reading (client) | Log in as a client and visit `/readings/birth-chart/delete/` | Redirected home with "Sorry only the site owner can do that." | Pass |
| Delete reading (logged out) | Log out and visit `/readings/birth-chart/delete/` | Redirected to the login page | Pass |

### Booking Testing

| Feature | Test | Expected | Result |
| ------- | ---- | -------- | ------ |
| Need to be logged into book |  Logged out and clicked "book" button birth chart reading | Redirected to the login page. Logged in and was taken back to the booking form| Pass |
| Booked slot disappears | As an admin, added one slot. As a client, booked it for a birth chart reading, then opened the booking form for a Sola Return| Success message with the date and time; the Solar Return forms shows "There are no times available right now" | Pass |
| Birth date cannot be in the future | Filled in booking form with future birth date | Error message displayed "Date of birth cannot be in the future." form not accepted | Pass |
| Cancelled booking moves to "Past and cancelled"| Cancelled a booking | Confirmation message displayed "Your (reading name) on (booking slot) has been cancelled. Redirected to my bookings and booking is now in "Past and cancelled | Pass |
| Cancelled booking releases slot | As a client, cancelled booking and then booked another reading | Cancelled slot was available to book into | Pass |
| No cancel button within 48 hours| As admin added slot for 24 ahead. As a client, booked it and opened My Bookings | No cancel button; message "Less than 48 hours to go, so this booking can't be changed online." | Pass |
| Other user can't cancel a booking | Logged in as another user typed `/bookings/5/cancel/` (the first client's booking) | 404 page with "No Booking matches the given query" | Pass |

## Validation Testing

### Python (PEP8)

All Python files were checked with flake8 locally and the CI Python Linter.
All pass with no errors.

![flake8 clean output](documentation/testing/flake8-clean.png)

| App | File | URL | Screenshot | Result |
| --- | ---- | --- | ---------- | -------|
| home | [tests.py](/home/tests.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/home/tests.py) | ![home tests validation](documentation/testing/validators/home-tests-validation.png) | Pass |
| home | [urls.py](/home/urls.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/home/urls.py) | ![home tests validation](documentation/testing/validators/home-urls-validation.png) | Pass |
| home | [views.py](/home/views.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/home/views.py) | ![home views validation](documentation/testing/validators/home-views-validation.png) | Pass |
| readings | [views.py](/readings/views.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/views.py) | ![readings views validation](documentation/testing/validators/readings-views-validation.png) | Pass |
| readings | [admin.py](/readings/admin.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/admin.py) | ![readings admin validation](documentation/testing/validators/readings-admin-validation.png) | Pass |
| readings | [forms.py](/readings/forms.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/forms.py) | ![readings forms validation](documentation/testing/validators/readings-forms-validation.png) | Pass |
| readings | [models.py](/readings/models.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/models.py) | ![readings models validation](documentation/testing/validators/readings-models-validation.png) | Pass |
| readings | [tests.py](/readings/tests.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/tests.py) | ![readings tests validation](documentation/testing/validators/readings-tests-validation.png) | Pass |
| readings | [urls.py](/readings/urls.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings/urls.py) | ![readings urls validation](documentation/testing/validators/readings-urls-validation.png) | Pass |
| bookings | [admin.py](/bookings/admin.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/admin.py) | ![bookings admin validation](documentation/testing/validators/bookings-admin-validation.png) | Pass |
| bookings | [forms.py](/bookings/forms.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/forms.py) | ![bookings forms validation](documentation/testing/validators/bookings-forms-validation.png) | Pass |
| bookings | [models.py](/bookings/models.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/models.py) | ![bookings models validation](documentation/testing/validators/bookings-models-validation.png) | Pass |
| bookings | [tests.py](/bookings/tests.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/tests.py) | ![bookings tests validation](documentation/testing/validators/bookings-tests-validation.png) | Pass |
| bookings | [urls.py](/bookings/urls.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/urls.py) | ![bookings urls validation](documentation/testing/validators/bookings-urls-validation.png) | Pass |
| bookings | [views.py](/bookings/views.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/bookings/views.py) | ![bookings views validation](documentation/testing/validators/bookings-views-validation.png) | Pass |
| checkout | [admin.py](/checkout/admin.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/admin.py) | ![checkout admin validation](documentation/testing/validators/checkout-admin-validation.png) | Pass |
| checkout | [models.py](/checkout/models.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/models.py) | ![checkout models validation](documentation/testing/validators/checkout-models-validation.png) | Pass |
| checkout | [payments.py](/checkout/payments.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/payments.py) | ![checkout payments validation](documentation/testing/validators/checkout-payments-validation.png) | Pass |
| checkout | [tests.py](/checkout/tests.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/tests.py) | ![checkout tests validation](documentation/testing/validators/checkout-tests-validation.png) | Pass |
| checkout | [urls.py](/checkout/urls.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/urls.py) | ![checkout urls validation](documentation/testing/validators/checkout-urls-validation.png) | Pass |
| checkout | [views.py](/checkout/views.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/views.py) | ![checkout views validation](documentation/testing/validators/checkout-views-validation.png) | Pass |
| checkout | [webhooks.py](/checkout/webhooks.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/checkout/webhooks.py) | ![checkout webhooks validation](documentation/testing/validators/checkout-webhooks-validation.png) | Pass |
| readings_with_rehanon | [urls.py](/readings_with_rehanon/urls.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings_with_rehanon/urls.py) | ![readings_with_rehanon urls validation](documentation/testing/validators/project-urls-validation.png) | Pass |
| readings_with_rehanon | [settings.py](/readings_with_rehanon/settings.py) | [PEP8 CI Link](https://pep8ci.herokuapp.com/https://raw.githubusercontent.com/Rehanon-Mackenzie/readings-with-rehanon/refs/heads/main/readings_with_rehanon/settings.py) | ![readings_with_rehanon settings validation](documentation/testing/validators/settings-validation.png) | Pass |