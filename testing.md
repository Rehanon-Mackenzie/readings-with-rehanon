### Bugs found by automated testing
| Test | What it caught | Fix |
| --- | --- | --- |
| `test_anonymous_user_sees_login_and_register_links` | The "Log in" link in the My Account dropdown had no text, so logged-out user saw a blank menu item. | Added the missing link text in `base.html`.|
| `test_admin_can_edit_a_reading`, `test_detail_page_shows_the_reading` | `super().save()` was indented inside the `if not self.slug:` block, so readings were only saved the first time. Edits silently did nothing. | Moved `super().save()` out of the `if` block so every save works. |

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

