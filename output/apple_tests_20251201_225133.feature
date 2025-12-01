# Auto-generated BDD Test Scenarios
# Source URL: https://www.apple.com/in/
# Generated: 2025-12-01T22:51:33.233025
# Generator: BDD Test Generator

Feature: Validate Popup Modals on Apple India Homepage

  Scenario: Verify "Learn more" popup
    Given User navigates to "https://www.apple.com/in/"
    When User clicks on "Learn more"
    Then Popup with title "Made with 30% recycled material by weight." is displayed

  Scenario: Verify "Learn more\n\t\t\t\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\t\t\t\t\tBuy" popup
    Given User navigates to "https://www.apple.com/in/"
    When User clicks on "Learn more\n\t\t\t\t\t\t\t\t\t\t\t\n\t\t\t\t\t\t\t\t\t\t\t\t\tBuy"
    Then Popup with title "Made with 30% recycled material by weight." is displayed

Feature: Validate Navigation Menu Hover Functionality on Apple India Homepage

  Scenario: Verify hover on "Apple"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Apple"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Store"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Store"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Mac"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Mac"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac" and click a link
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac"
    Then Dropdown menu is displayed
    When User clicks on "Shop Gifts" link
    Then User is redirected to "https://www.apple.com/in/shop/goto/store"

  Scenario: Verify hover on "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac" and clicks "Find a Store"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac"
    Then Dropdown menu is displayed
    When User clicks on "Find a Store" link
    Then User is redirected to "https://www.apple.com/in/retail/"

  Scenario: Verify hover on "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac" and clicks "Gift Cards"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac"
    Then Dropdown menu is displayed
    When User clicks on "Gift Cards" link
    Then User is redirected to "https://www.apple.com/in/shop/goto/giftcards"

  Scenario: Verify hover on "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac" and clicks "AirPods"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac"
    Then Dropdown menu is displayed
    When User clicks on "AirPods" link
    Then User is redirected to "https://www.apple.com/in/airpods/"

  Scenario: Verify hover on "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac" and clicks "Apple Trade In"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "StoreShopShop GiftsMaciPadiPhoneApple WatchAirPodsAccessoriesQuick LinksFind a StoreOrder StatusApple Trade InWays to BuyPersonal SetupShop Special StoresEducationBusinessMacExplore MacExplore All Mac"
    Then Dropdown menu is displayed
    When User clicks on "Apple Trade In" link
    Then User is redirected to "https://www.apple.com/in/shop/goto/trade_in"

  Scenario: Verify hover on "iPad"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "iPad"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "iPhone"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "iPhone"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Watch"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Watch"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "AirPods"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "AirPods"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "TV & Home"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "TV & Home"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "AirTag"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "AirTag"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Accessories"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Accessories"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Gift Cards"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Gift Cards"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Wallet"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Wallet"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Manage Your Apple Account"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Manage Your Apple Account"
    Then No dropdown menu is displayed

  Scenario: Verify hover on "Apple Store Account"
    Given User navigates to "https://www.apple.com/in/"
    When User hovers over "Apple Store Account"
    Then No dropdown menu is displayed