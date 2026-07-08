from django.test import SimpleTestCase
from django.urls import reverse


class HomeworkUrlTests(SimpleTestCase):
    def test_delete_assignment_reverse_works(self):
        url = reverse('homework:delete_assignment', args=[42])
        self.assertEqual(url, '/homework/assignments/42/delete/')
