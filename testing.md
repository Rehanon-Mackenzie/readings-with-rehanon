### Bugs found by automated testing
| Test | What it caught | Fix |
| --- | --- | --- |
|`test_anonymous_user_sees_login_and_register_links` | The "Log in" link in the My Account dropdown had no text, so logged-out user saw a blank menu item. | Added the missing link text in `base.html`.|