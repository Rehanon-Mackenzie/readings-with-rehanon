from datetime import timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import AvailabilitySlot


class AvailabilitySlotTests(TestCase):
    """Tests for the AvailabilitySlot model."""

    def setUp(self):
        self.start = timezone.now() + timedelta(days=7)
    
    def test_valid_future_slot_passes_validation(self):
        slot = AvailabilitySlot(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        slot.full_clean()  # raises an error if the slot is invalid
        
    def test_end_time_before_start_time_is_rejected(self):
        slot = AvailabilitySlot(
            start_time=self.start, end_time=self.start - timedelta(hours=1))
        with self.assertRaises(ValidationError):
            slot.full_clean()
            
    def test_slot_in_the_past_is_rejected(self):
        past = timezone.now() - timedelta(days=1)
        slot = AvailabilitySlot(start_time=past, end_time=past + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            slot.full_clean()
    
    def test_new_slot_is_not_booked(self):
        slot = AvailabilitySlot.objects.create(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        self.assertFalse(slot.is_booked)
        
    def test_slots_are_ordered_by_start_time(self):
        later = AvailabilitySlot.objects.create(
            start_time=self.start + timedelta(days=1),
            end_time=self.start + timedelta(days=1, hours=1))
        earlier = AvailabilitySlot.objects.create(
            start_time=self.start, end_time=self.start + timedelta(hours=1))
        self.assertEqual(list(AvailabilitySlot.objects.all()), [earlier, later])