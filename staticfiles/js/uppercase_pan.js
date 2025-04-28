document.addEventListener('DOMContentLoaded', function () {
  const panField = document.querySelector('input[name="pan_number"]');

  if (panField) {
    // Convert to uppercase on focus
    panField.addEventListener('focus', function () {
      this.value = this.value.toUpperCase();
    });

    // Convert to uppercase as the user types
    panField.addEventListener('input', function () {
      this.value = this.value.toUpperCase();
    });
  }
});