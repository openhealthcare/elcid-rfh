from opal.core.test import OpalTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from opal.models import Role

class ElcidUserAdminFormTestCase(OpalTestCase):
    """
    Elcid overwrites the opal user admin to make sure that
    we can't have duplicate emails.

    This unit test also checks that the opal user profile
    logic still works, ie that we have inheritance set up
    correctly.
    """
    def setUp(self):
        # initialise the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.new_user = User.objects.create(username="test_user")
        self.new_user.set_password("test1")
        self.new_user.save()
        self.add_url = reverse('admin:auth_user_add')
        self.change_url = reverse(
            'admin:auth_user_change', args=(self.new_user.pk,)
        )
        self.role = Role.objects.create(name="can_doctor")


    def test_post_create_user_success(self):
        """
        Tests that we can create a user and user profile
        """
        post_dict = {
            # profile fields
             '_save': ['Save'],
            'profile-MIN_NUM_FORMS': ['0'],
            'profile-TOTAL_FORMS': ['1'],
            'profile-MAX_NUM_FORMS': ['1'],
            'profile-__prefix__-id': [''],
            'profile-0-id': [''],
            'profile-0-roles': [self.role.id],
            'profile-0-user': [''],
            'profile-INITIAL_FORMS': ['0'],
            'profile-__prefix__-force_password_change': ['on'],

            # user fields
            'username': ['create_user'],
            'email': ['some_email@nhs.com'],
            'password1': ['test1'],
            'password2': ['test1'],
            'first_name': [''],
            'last_name': [''],
        }
        self.client.post(self.add_url, post_dict)
        new_user = User.objects.filter(username='create_user').first()
        # a user should have been created
        self.assertIsNotNone(new_user)
        # the user's user profile should have the role can_doctor
        self.assertEqual(
            list(new_user.profile.roles.values_list('name', flat=True)),
            ["can_doctor"]
        )

    def test_post_create_user_email_error(self):
        post_dict = {
            # profile fields
             '_save': ['Save'],
            'profile-MIN_NUM_FORMS': ['0'],
            'profile-TOTAL_FORMS': ['1'],
            'profile-MAX_NUM_FORMS': ['1'],
            'profile-__prefix__-id': [''],
            'profile-0-id': [''],
            'profile-0-roles': [self.role.id],
            'profile-0-user': [''],
            'profile-INITIAL_FORMS': ['0'],
            'profile-__prefix__-force_password_change': ['on'],

            # user fields
            'username': ['create_user'],
            'email': ['someone@nhs.net'],
            'password1': ['test1'],
            'password2': ['test1'],
            'first_name': [''],
            'last_name': [''],
        }
        User.objects.create(
            username='existing_user', email='someone@nhs.net'
        )

        new_user = User.objects.filter(username='create_user').first()
        response = self.client.post(self.add_url, post_dict)
        self.assertEqual(
            response.context['adminform'].errors,
            {'email': ['Email is currently in use by existing_user']}
        )
        # a user should have been created
        self.assertIsNone(new_user)

    def test_post_edit_user_success(self):
        post_dict = {
            '_save': ['Save'],
            'first_name': [''],
            'username': ['edit_user'],
            'password1': ['test1'],
            'password2': ['test1'],
            'last_name': [''],
            'email': [''],
            'last_login_0': [''],
            'last_login_1': [''],
            'date_joined_0': ['02/08/2019'],
            'date_joined_1': ['14:21:00'],
            'initial-date_joined_0': ['02/08/2019'],
            'initial-date_joined_1': ['14:21:00'],
            'is_active': ['on'],
            'profile-TOTAL_FORMS': ['1'],
            'profile-MAX_NUM_FORMS': ['1'],
            'profile-INITIAL_FORMS': ['1'],
            'profile-__prefix__-id': [''],
            'profile-__prefix__-user': [self.new_user.pk],
            'profile-0-force_password_change': ['on'],
            'profile-0-id': [self.new_user.profile.id],
            'profile-0-user': [self.new_user.id],
            'profile-0-roles': [self.role.id],
            'profile-__prefix__-force_password_change': ['on'],
            'profile-MIN_NUM_FORMS': ['0'],
        }
        self.client.post(self.change_url, post_dict)
        reloaded_user = User.objects.get(username="edit_user")
        self.assertEqual(
            list(reloaded_user.profile.roles.values_list('name', flat=True)),
            ["can_doctor"]
        )

    def test_post_edit_user_email_error(self):
        User.objects.create(
            username='existing_user', email='someone@nhs.net'
        )

        post_dict = {
            '_save': ['Save'],
            'first_name': [''],
            'username': ['edit_user'],
            'password1': ['test1'],
            'password2': ['test1'],
            'last_name': [''],
            'email': ['someone@nhs.net'],
            'last_login_0': [''],
            'last_login_1': [''],
            'date_joined_0': ['02/08/2019'],
            'date_joined_1': ['14:21:00'],
            'initial-date_joined_0': ['02/08/2019'],
            'initial-date_joined_1': ['14:21:00'],
            'is_active': ['on'],
            'profile-TOTAL_FORMS': ['1'],
            'profile-MAX_NUM_FORMS': ['1'],
            'profile-INITIAL_FORMS': ['1'],
            'profile-__prefix__-id': [''],
            'profile-__prefix__-user': [self.new_user.pk],
            'profile-0-force_password_change': ['on'],
            'profile-0-id': [self.new_user.profile.id],
            'profile-0-user': [self.new_user.id],
            'profile-0-roles': [self.role.id],
            'profile-__prefix__-force_password_change': ['on'],
            'profile-MIN_NUM_FORMS': ['0'],
        }
        new_user = User.objects.filter(username='edit_user').first()
        response = self.client.post(self.add_url, post_dict)
        self.assertEqual(
            response.context['adminform'].errors,
            {'email': ['Email is currently in use by existing_user']}
        )
        # a user should have been created
        self.assertIsNone(new_user)
