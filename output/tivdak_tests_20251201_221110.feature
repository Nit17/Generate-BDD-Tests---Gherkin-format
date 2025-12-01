# Auto-generated BDD Test Scenarios
# Source URL: https://www.tivdak.com/patient-stories/
# Generated: 2025-12-01T22:11:10.591512
# Generator: BDD Test Generator

Feature: Validate Hover Navigation on Patient Stories Page

  Background:
    Given User navigates to "https://www.tivdak.com/patient-stories/"
    Then Page title should be "Patient Stories | Tivdak® (tisotumab vedotin-tftv)"

  Scenario: Verify "About Tivdak" hover menu and navigation

    When User hovers over "About Tivdak"
    Then Dropdown menu should be visible
    And Link "Tivdak and You" with href "https://www.tivdak.com/about-tivdak/" should be visible
    And Link "What Is Tivdak?" with href "https://www.tivdak.com/about-tivdak/" should be visible

    When User clicks "Tivdak and You"
    Then User should be redirected to "https://www.tivdak.com/about-tivdak/"

  Scenario: Verify "Results" hover menu and navigation

    Given User navigates to "https://www.tivdak.com/patient-stories/"
    When User hovers over "Results"
    Then Dropdown menu should be visible
    And Link "Overall Survival" with href "https://www.tivdak.com/study-results/" should be visible
    And Link "Objective Response" with href "https://www.tivdak.com/study-results/" should be visible
    And Link "Understanding the Data" with href "https://www.tivdak.com/study-results/understanding-the-data/" should be visible

    When User clicks "Overall Survival"
    Then User should be redirected to "https://www.tivdak.com/study-results/"

  Scenario: Verify "Support" hover menu and navigation

    Given User navigates to "https://www.tivdak.com/patient-stories/"
    When User hovers over "Support"
    Then Dropdown menu should be visible
    And Link "Downloads" with href "https://www.tivdak.com/resources-and-support/" should be visible
    And Link "Pfizer Oncology Together™" with href "https://www.tivdak.com/resources-and-support/" should be visible
    And Link "TivdakTexts" with href "https://www.tivdak.com/resources-and-support/" should be visible
    And Link "Advocacy Groups" with href "https://www.tivdak.com/resources-and-support/" should be visible
    And Link "Support Videos" with href "https://www.tivdak.com/resources-and-support/support-videos/" should be visible

    When User clicks "Support Videos"
    Then User should be redirected to "https://www.tivdak.com/resources-and-support/support-videos/"