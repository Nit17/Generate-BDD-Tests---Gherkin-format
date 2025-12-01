# Auto-generated BDD Test Scenarios
# Source URL: https://www.tivdak.com/patient-stories/
# Generated: 2024-12-01
# Generator: BDD Test Generator

Feature: Validate "Learn More" pop-up functionality

  Scenario: Verify the cancel button in the "You are now leaving tivdak.com" pop-up
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user clicks the "Learn More" button
    Then a pop-up should appear with the title "You are now leaving tivdak.com"
    When the user clicks the "Cancel" button
    Then the pop-up should close and the user should remain on the same page

  Scenario: Verify the continue button navigates to external site
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user clicks the "Learn More" button
    Then a pop-up should appear with the title "You are now leaving tivdak.com"
    When the user clicks the "Continue" button
    Then the page URL should change to "https://alishasjourney.com/"


Feature: Validate navigation menu functionality

  Scenario: Verify navigation from "Patient Stories" to "What is Tivdak?" page
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "About Tivdak"
    And a dropdown menu should appear
    And clicks the link "What is Tivdak?" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/about-tivdak/"

  Scenario: Verify hover dropdown reveals all submenu items
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "About Tivdak"
    Then a dropdown menu should appear with multiple options
    And the dropdown should contain "What is Tivdak?"
    And the dropdown should contain "How Tivdak Works"
    And the dropdown should contain "Clinical Trial Results"
