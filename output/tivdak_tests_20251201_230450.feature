# Auto-generated BDD Test Scenarios
# Source URL: https://www.tivdak.com/patient-stories/
# Generated: 2025-12-01T23:04:50.503611
# Generator: BDD Test Generator

Feature: Patient Stories Page Interactions - Tivdak

  Scenario: Verify "About Tivdak" hover dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over "About Tivdak"
    Then a dropdown should appear
    And the dropdown should contain the link "Tivdak and You" with href "https://www.tivdak.com/about-tivdak/"
    And the dropdown should contain the link "What Is Tivdak?" with href "https://www.tivdak.com/about-tivdak/"

  Scenario: Verify "Results" hover dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over "Results"
    Then a dropdown should appear
    And the dropdown should contain the link "Overall Survival" with href "https://www.tivdak.com/study-results/"
    And the dropdown should contain the link "Objective Response" with href "https://www.tivdak.com/study-results/"
    And the dropdown should contain the link "Understanding the Data" with href "https://www.tivdak.com/study-results/understanding_the_data/"

  Scenario: Verify "Support" hover dropdown
    Given the user is on the "https://www.tivdak.com/patient-stories/" page
    When the user hovers over "Support"
    Then a dropdown should appear
    And the dropdown should contain the link "Downloads" with href "https://www.tivdak.com/resources-and-support/"
    And the dropdown should contain the link "Pfizer Oncology Together™" with href "https://www.tivdak.com/resources-and-support/"
    And the dropdown should contain the link "TivdakTexts" with href "https://www.tivdak.com/resources-and-support/"
    And the dropdown should contain the link "Advocacy Groups" with href "https://www.tivdak.com/resources-and-support/"
    And the dropdown should contain the link "Support Videos" with href "https://www.tivdak.com/resources-and-support/support-videos/"