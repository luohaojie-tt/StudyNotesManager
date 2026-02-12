"""
E2E tests for user workflows using Playwright.

These tests simulate complete user journeys through the application.
"""
import pytest
from playwright.async_api import Page
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



@pytest.mark.e2e
@pytest.mark.slow
class TestUserRegistrationWorkflow:
    """Test complete user registration and onboarding flow."""

    @pytest.mark.asyncio
    async def test_new_user_registration(self, page: Page):
        """Test registering a new user and logging in."""
        # Navigate to registration page
        await page.goto(f"{BASE_URL}/register")

        # Fill registration form
        await page.fill("input[name='email']", "e2e@example.com")
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")
        await page.fill("input[name='confirmPassword']", "SecurePass123!")
        await page.fill("input[name='fullName']", "E2E Test User")

        # Submit form
        await page.click("button[type='submit']")

        # Should redirect to dashboard
        await page.wait_for_url("**/dashboard")
        assert await page.title() == "Dashboard - StudyNotesManager"

        # Verify welcome message
        welcome_text = await page.text_content("h1")
        assert "Welcome" in welcome_text or "Dashboard" in welcome_text

    @pytest.mark.asyncio
    async def test_login_logout_flow(self, page: Page):
        """Test logging in and logging out."""
        # Go to login page
        await page.goto(f"{BASE_URL}/login")

        # Fill login form
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")

        # Submit
        await page.click("button[type='submit']")

        # Wait for dashboard
        await page.wait_for_url("**/dashboard")

        # Click logout
        await page.click("button[aria-label='Logout']")

        # Should redirect to login page
        await page.wait_for_url("**/login")
        assert await page.locator("input[name='username']").is_visible()


@pytest.mark.e2e
@pytest.mark.slow
class TestNoteManagementWorkflow:
    """Test complete note management workflow."""

    @pytest.fixture
    async def authenticated_page(self, browser):
        """Create authenticated page for testing."""
        context = await browser.new_context()
        page = await context.new_page()

        # Login first
        await page.goto(f"{BASE_URL}/login")
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")

        yield page

        await context.close()

    @pytest.mark.asyncio
    async def test_create_and_view_note(self, authenticated_page: Page):
        """Test creating a note and viewing it."""
        page = authenticated_page

        # Click "Create Note" button
        await page.click("button:has-text('Create Note')")

        # Wait for note form
        await page.wait_for_selector("input[name='title']")

        # Fill note details
        await page.fill("input[name='title']", "E2E Test Note")
        await page.fill("textarea[name='content']", "This is an E2E test note content")
        await page.select_option("select[name='subject']", "Mathematics")

        # Add tags
        tags_input = page.locator("input[name='tags']")
        await tags_input.fill("algebra")
        await page.keyboard.press("Enter")
        await tags_input.fill("equations")
        await page.keyboard.press("Enter")

        # Save note
        await page.click("button:has-text('Save')")

        # Wait for success message
        await page.wait_for_selector("text=Note created successfully")

        # Navigate to notes list
        await page.click("a:has-text('Notes')")

        # Verify note appears in list
        assert await page.locator("text=E2E Test Note").is_visible()

    @pytest.mark.asyncio
    async def test_edit_note(self, authenticated_page: Page):
        """Test editing an existing note."""
        page = authenticated_page

        # Go to notes page
        await page.goto(f"{BASE_URL}/notes")

        # Click on first note
        await page.click(".note-card:first-child")

        # Wait for note detail page
        await page.wait_for_selector("button:has-text('Edit')")

        # Click edit
        await page.click("button:has-text('Edit')")

        # Modify content
        await page.fill("textarea[name='content']", "Updated E2E test content")

        # Save changes
        await page.click("button:has-text('Save')")

        # Verify update
        await page.wait_for_selector("text=Note updated successfully")
        assert await page.locator("text=Updated E2E test content").is_visible()

    @pytest.mark.asyncio
    async def test_delete_note(self, authenticated_page: Page):
        """Test deleting a note."""
        page = authenticated_page

        # Go to notes page
        await page.goto(f"{BASE_URL}/notes")

        # Get initial note count
        initial_count = await page.locator(".note-card").count()

        # Delete first note
        await page.hover(".note-card:first-child")
        await page.click(".note-card:first-child button[aria-label='Delete']")

        # Confirm deletion
        await page.click("button:has-text('Confirm')")

        # Wait for success message
        await page.wait_for_selector("text=Note deleted successfully")

        # Verify note count decreased
        final_count = await page.locator(".note-card").count()
        assert final_count == initial_count - 1


@pytest.mark.e2e
@pytest.mark.slow
class TestQuizWorkflow:
    """Test quiz generation and answering workflow."""

    @pytest.fixture
    async def authenticated_page(self, browser):
        """Create authenticated page with a note."""
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto(f"{BASE_URL}/login")
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")

        # Create a test note first
        await page.click("button:has-text('Create Note')")
        await page.wait_for_selector("input[name='title']")
        await page.fill("input[name='title']", "Algebra Quiz Note")
        await page.fill("textarea[name='content']", "Linear equations are equations of the first degree. To solve 2x + 3 = 7, subtract 3 from both sides to get 2x = 4, then divide by 2 to get x = 2.")
        await page.select_option("select[name='subject']", "Mathematics")
        await page.click("button:has-text('Save')")
        await page.wait_for_selector("text=Note created successfully")

        yield page

        await context.close()

    @pytest.mark.asyncio
    async def test_generate_quiz_from_note(self, authenticated_page: Page):
        """Test generating a quiz from a note."""
        page = authenticated_page

        # Go to notes page
        await page.goto(f"{BASE_URL}/notes")

        # Click on note
        await page.click(".note-card:first-child")

        # Generate quiz
        await page.click("button:has-text('Generate Quiz')")

        # Wait for quiz generation
        await page.wait_for_selector("text=Quiz generated successfully")

        # Verify quiz appears
        assert await page.locator(".quiz-question").is_visible()

    @pytest.mark.asyncio
    async def test_answer_quiz(self, authenticated_page: Page):
        """Test answering quiz questions."""
        page = authenticated_page

        # Generate quiz first
        await page.goto(f"{BASE_URL}/notes")
        await page.click(".note-card:first-child")
        await page.click("button:has-text('Generate Quiz')")
        await page.wait_for_selector(".quiz-question")

        # Answer questions
        for i in range(5):
            question = page.locator(f".quiz-question >> nth={i}")
            await question.wait_for()

            # Select first option
            await question.locator("input[type='radio'] >> nth=0").check()

        # Submit quiz
        await page.click("button:has-text('Submit Quiz')")

        # Wait for results
        await page.wait_for_selector("text=Quiz Results")

        # Verify score is displayed
        assert await page.locator("text=Score:").is_visible()

    @pytest.mark.asyncio
    async def test_view_incorrect_answers(self, authenticated_page: Page):
        """Test viewing incorrect answers and explanations."""
        page = authenticated_page

        # Generate and submit quiz
        await page.goto(f"{BASE_URL}/notes")
        await page.click(".note-card:first-child")
        await page.click("button:has-text('Generate Quiz')")
        await page.wait_for_selector(".quiz-question")

        # Answer all questions incorrectly (select last option)
        questions = await page.locator(".quiz-question").count()
        for i in range(questions):
            question = page.locator(f".quiz-question >> nth={i}")
            options = await question.locator("input[type='radio']").count()
            await question.locator(f"input[type='radio'] >> nth={options-1}").check()

        await page.click("button:has-text('Submit Quiz')")
        await page.wait_for_selector("text=Quiz Results")

        # Check if incorrect answers are shown
        assert await page.locator(".incorrect-answer").count() > 0

        # Verify explanations are shown
        assert await page.locator("text=Explanation:").is_visible()


@pytest.mark.e2e
@pytest.mark.slow
class TestMindmapWorkflow:
    """Test mindmap generation and visualization."""

    @pytest.fixture
    async def authenticated_page(self, browser):
        """Create authenticated page."""
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto(f"{BASE_URL}/login")
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")

        yield page

        await context.close()

    @pytest.mark.asyncio
    async def test_generate_mindmap_from_note(self, authenticated_page: Page):
        """Test generating mindmap from a note."""
        page = authenticated_page

        # Create note
        await page.click("button:has-text('Create Note')")
        await page.wait_for_selector("input[name='title']")
        await page.fill("input[name='title']", "Physics Mindmap")
        await page.fill("textarea[name='content']", "Newton's laws of motion describe the relationship between forces and motion. The first law states that an object at rest stays at rest, and an object in motion stays in motion unless acted upon by an external force.")
        await page.select_option("select[name='subject']", "Physics")
        await page.click("button:has-text('Save')")
        await page.wait_for_selector("text=Note created successfully")

        # Generate mindmap
        await page.click("button:has-text('Generate Mindmap')")

        # Wait for mindmap
        await page.wait_for_selector("text=Mindmap generated successfully")

        # Verify mindmap visualization
        assert await page.locator(".mindmap-canvas").is_visible()
        assert await page.locator(".mindmap-node").count() > 0

    @pytest.mark.asyncio
    async def test_interactive_mindmap(self, authenticated_page: Page):
        """Test interacting with mindmap nodes."""
        page = authenticated_page

        # Go to existing mindmap
        await page.goto(f"{BASE_URL}/notes")
        await page.click(".note-card:first-child")
        await page.click("button:has-text('View Mindmap')")

        # Wait for mindmap to load
        await page.wait_for_selector(".mindmap-canvas")

        # Click on a node
        node = page.locator(".mindmap-node >> nth=0")
        await node.click()

        # Verify node details appear
        assert await page.locator(".node-details").is_visible()

        # Test zoom functionality
        await page.mouse.wheel(0, -100)  # Scroll up to zoom in
        await page.wait_for_timeout(500)  # Wait for zoom animation

        # Test pan functionality
        await page.mouse.down()
        await page.mouse.move(100, 100)
        await page.mouse.up()


@pytest.mark.e2e
@pytest.mark.slow
class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self, page: Page):
        """Test application behavior with network errors."""
        # Simulate offline mode
        await page.context.set_offline(True)

        await page.goto(f"{BASE_URL}/login")

        # Try to login (should fail gracefully)
        await page.fill("input[name='username']", "e2euser")
        await page.fill("input[name='password']", "SecurePass123!")
        await page.click("button[type='submit']")

        # Should show error message
        await page.wait_for_selector("text=Network error")

        # Restore connection
        await page.context.set_offline(False)

    @pytest.mark.asyncio
    async def test_form_validation_errors(self, page: Page):
        """Test form validation for invalid inputs."""
        await page.goto(f"{BASE_URL}/register")

        # Submit empty form
        await page.click("button[type='submit']")

        # Should show validation errors
        assert await page.locator("text=Email is required").is_visible()
        assert await page.locator("text=Password is required").is_visible()

        # Test invalid email
        await page.fill("input[name='email']", "invalid-email")
        await page.click("button[type='submit']")

        assert await page.locator("text=Invalid email format").is_visible()

        # Test weak password
        await page.fill("input[name='email']", "test@example.com")
        await page.fill("input[name='password']", "weak")
        await page.click("button[type='submit']")

        assert await page.locator("text=Password must be at least 8 characters").is_visible()
