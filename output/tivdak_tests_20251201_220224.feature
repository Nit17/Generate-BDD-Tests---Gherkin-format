# Auto-generated BDD Test Scenarios
# Source URL: https://www.tivdak.com/patient-stories/
# Generated: 2025-12-01T22:02:24.406043
# Generator: BDD Test Generator


Feature: Validate navigation menu functionality

  Scenario: Verify hover menu for 'About Tivdak'
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "About Tivdak"
    Then a dropdown should appear
    When the user clicks the link "Tivdak and You" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/about-tivdak/"

  Scenario: Verify hover menu for 'Results'
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "Results"
    Then a dropdown should appear
    When the user clicks the link "Overall Survival" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/study-results/"

  Scenario: Verify hover menu for 'Support'
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over the navigation menu "Support"
    Then a dropdown should appear
    When the user clicks the link "Downloads" from the dropdown
    Then the page URL should change to "https://www.tivdak.com/resources-and-support/"
