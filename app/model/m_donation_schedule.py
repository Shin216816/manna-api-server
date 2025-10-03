# REMOVED: DonationSchedule model and related enums
# This model is not needed for the roundup-only donation system.
# Roundup donations are triggered automatically by Plaid transactions,
# not by scheduled donations. All donation settings are handled by DonationPreference.
#
# The donation_schedules table will be dropped by the remove_donation_schedule_table.py migration.
#
# For roundup settings, use:
# - app.model.m_donation_preference.DonationPreference
