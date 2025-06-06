import streamlit as st
import os
import time
import asyncio
from io import BytesIO
import tempfile

# Configure page
st.set_page_config(
    page_title="AI Video Generator",
    page_icon="🎬",
    layout="wide"
)

# Title and description
st.title("🎬 AI Kling Video Generator")
st.markdown("Generate high-quality videos from text descriptions using Kling AI")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input(
        "FAL API Key",
        type="password",
        help="Enter your fal.ai API key"
    )
    
    if not api_key:
        st.warning("Please enter your FAL API key to continue")
        st.info("You can get your API key from [fal.ai](https://fal.ai)")

# Function to setup fal client
def setup_fal_client(api_key):
    try:
        import fal_client as fal
        
        # Configure the client with API key
        os.environ['FAL_KEY'] = api_key
        
        return fal
    except ImportError:
        st.error("fal-client is not installed. Please install it using: pip install fal-client")
        return None

# Helper function to extract video URL from result
def extract_video_url(result):
    """Extract video URL from API result"""
    if not result:
        return None
    
    video_url = None
    
    # Try different ways to extract video URL
    if hasattr(result, 'video') and result.video:
        # Case 1: result.video exists
        if isinstance(result.video, dict):
            video_url = result.video.get('url')
        elif isinstance(result.video, str):
            video_url = result.video
        else:
            video_url = str(result.video)
    elif hasattr(result, 'video_url'):
        # Case 2: result.video_url exists
        video_url = result.video_url
    elif hasattr(result, 'url'):
        # Case 3: result.url exists
        video_url = result.url
    elif isinstance(result, dict):
        # Case 4: result is a dictionary
        video_url = result.get('video', {}).get('url') or result.get('video_url') or result.get('url')
    
    return video_url

# Helper function to display video result
def display_video_result(result):
    """Display video result with debug info and download options"""
    # Debug: Print the result structure
    st.write("**Debug Info:**")
    st.write("Result type:", type(result))
    if result:
        st.write("Result attributes:", dir(result))
        st.write("Result content:", result)
    
    # Display result
    if result:
        video_url = extract_video_url(result)
        
        if video_url:
            st.success("🎉 Video generated successfully!")
            st.video(video_url)
            st.markdown(f"[📥 Download Video]({video_url})")
            
            # Show additional info if available
            if hasattr(result, 'seed'):
                st.info(f"Seed: {result.seed}")
            elif isinstance(result, dict) and 'seed' in result:
                st.info(f"Seed: {result['seed']}")
                
            if hasattr(result, 'timings'):
                st.info(f"Processing time: {result.timings}")
            elif isinstance(result, dict) and 'timings' in result:
                st.info(f"Processing time: {result['timings']}")
        else:
            st.error("Video URL not found in response")
            st.write("Available keys in result:", list(result.keys()) if isinstance(result, dict) else "Not a dictionary")
    else:
        st.error("No result returned from API")

# Function to generate video using fal.subscribe (blocking)
def generate_video_blocking(fal, prompt):
    try:
        import fal_client
        
        # Define queue update handler
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    if isinstance(log, dict) and "message" in log:
                        st.text(f"📝 {log['message']}")
                    elif hasattr(log, 'message'):
                        st.text(f"📝 {log.message}")
        
        with st.spinner("🎬 Generating video... This may take several minutes."):
            progress_placeholder = st.empty()
            log_container = st.container()
            
            with log_container:
                st.info("🔄 Processing video generation...")
                
                result = fal_client.subscribe(
                    "fal-ai/kling-video/v2/master/text-to-video",
                    arguments={
                        "prompt": prompt
                    },
                    with_logs=True,
                    on_queue_update=on_queue_update,
                )
                
                # Clear progress indicators
                progress_placeholder.empty()
                
                return result
            
    except ImportError:
        st.error("fal_client module not found. Please install it using: pip install fal-client")
        return None
    except Exception as e:
        st.error(f"Failed to generate video: {str(e)}")
        st.exception(e)
        return None

# Function to handle queue updates
def handle_queue_update(update, progress_placeholder, log_placeholder):
    if hasattr(update, 'status'):
        if update.status == "IN_PROGRESS":
            with progress_placeholder.container():
                st.info(f"🔄 Status: {update.status}")
            
            if hasattr(update, 'logs') and update.logs:
                latest_logs = update.logs[-3:]  # Show last 3 log messages
                log_text = "\n".join([log.message for log in latest_logs if hasattr(log, 'message')])
                if log_text:
                    with log_placeholder.container():
                        st.text(log_text)
        
        elif update.status == "IN_QUEUE":
            with progress_placeholder.container():
                st.info(f"⏳ Status: {update.status} - Waiting in queue...")

# Function to generate video using queue method (non-blocking)
def generate_video_queue(fal, prompt):
    try:
        import fal_client
        
        # Define queue update handler based on your code pattern
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    if isinstance(log, dict) and "message" in log:
                        st.text(f"📝 {log['message']}")
                    elif hasattr(log, 'message'):
                        st.text(f"📝 {log.message}")
        
        # Use fal_client.subscribe with your code pattern
        with st.spinner("🎬 Generating video using queue method..."):
            progress_placeholder = st.empty()
            log_container = st.container()
            
            with log_container:
                st.info("🔄 Processing video generation...")
                
                result = fal_client.subscribe(
                    "fal-ai/kling-video/v2/master/text-to-video",
                    arguments={
                        "prompt": prompt
                    },
                    with_logs=True,
                    on_queue_update=on_queue_update,
                )
                
                # Clear progress indicators
                progress_placeholder.empty()
                
                return result
        
    except ImportError:
        st.error("fal_client module not found. Please install it using: pip install fal-client")
        return None
    except Exception as e:
        st.error(f"Failed to generate video: {str(e)}")
        st.exception(e)
        return None

# Main content area
if api_key:
    # Setup fal client
    fal = setup_fal_client(api_key)
    
    if fal:
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("🎬 Video Generation Input")
            
            # Video prompt input
            prompt = st.text_area(
                "Video Description Prompt",
                placeholder="Describe the video you want to generate in detail...",
                help="Enter a detailed description of the video scene you want to create",
                height=200,
                value="""Wide establishing shot of busy city street during afternoon, diverse people walking with purpose, warm natural lighting establishing urban community setting where people often overlook each other's needs."""
            )
            
            # Method selection
            method = st.radio(
                "Generation Method",
                ["Blocking (Recommended)", "Queue Method"],
                help="Blocking method waits for completion, Queue method allows monitoring"
            )
            
            # Generate button
            generate_button = st.button(
                "🎬 Generate Video",
                type="primary",
                disabled=not prompt.strip()
            )
        
        with col2:
            st.header("🎥 Output")
            
            # Check if generate button was clicked and handle generation
            if 'generate_button' in locals() and generate_button:
                try:
                    # Generate social awareness short film scenes
                    st.success("🤝 Starting Social Awareness Short Film Generation...")
                    scenes = st.session_state.get('custom_scenes', [
                        "Wide establishing shot of busy city street during afternoon, diverse people walking with purpose, warm natural lighting establishing urban community setting where people often overlook each other",
                        "Medium close-up of elderly woman struggling with heavy grocery bags at bus stop, looking tired and overwhelmed, other people passing by without noticing her difficulty",
                        "Close-up reaction shot of young man in casual clothes noticing the elderly woman's struggle, his expression changing from distracted to concerned and empathetic, deciding to help",
                        "Medium shot sequence showing the young man approaching and offering help, gentle smile and respectful gesture, elderly woman's grateful surprised expression as she accepts assistance",
                        "Heartwarming medium two-shot of them working together, him carrying her bags while they walk and chat, showing genuine human connection and kindness between strangers",
                        "Final wide shot pulling back to reveal other people nearby inspired by this act, beginning to help others around them, creating ripple effect of kindness throughout the community"
                    ])
                    
                    # Generate each scene
                    video_results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, scene_prompt in enumerate(scenes):
                        status_text.text(f"Generating Scene {i+1}/6: {scene_prompt[:50]}...")
                        progress_bar.progress((i) / len(scenes))
                        
                        try:
                            if method == "Blocking (Recommended)":
                                result = generate_video_blocking(fal, scene_prompt)
                            else:
                                result = generate_video_queue(fal, scene_prompt)
                            
                            if result:
                                video_results.append({
                                    'scene': i+1,
                                    'prompt': scene_prompt,
                                    'result': result
                                })
                                st.success(f"✅ Scene {i+1} completed!")
                            else:
                                st.error(f"❌ Scene {i+1} failed to generate")
                                
                        except Exception as e:
                            st.error(f"❌ Scene {i+1} error: {str(e)}")
                    
                    progress_bar.progress(1.0)
                    status_text.text("🎉 All social awareness scenes completed!")
                    
                    # Display all generated videos
                    st.header("🤝 Your Social Awareness Short Film")
                    st.markdown("**Here are all 6 scenes of your social awareness film:**")
                    
                    # Create columns for better layout
                    cols = st.columns(2)
                    
                    for i, video_data in enumerate(video_results):
                        col = cols[i % 2]
                        
                        with col:
                            st.subheader(f"Scene {video_data['scene']}")
                            st.text(f"{video_data['prompt'][:100]}...")
                            
                            # Extract and display video
                            video_url = extract_video_url(video_data['result'])
                            if video_url:
                                st.video(video_url)
                                st.markdown(f"[📥 Download Scene {video_data['scene']}]({video_url})")
                            else:
                                st.error("Video URL not found")
                    
                    # Instructions for combining videos
                    st.info("""
                    🎞️ **To create your final 30-second social awareness film:**
                    1. Download all 6 scene videos
                    2. Use video editing software (e.g., DaVinci Resolve, Adobe Premiere, or free tools like OpenShot)
                    3. Import all scenes in order (Scene 1 → 2 → 3 → 4 → 5 → 6)
                    4. Add smooth transitions between scenes
                    5. Consider adding inspiring background music
                    6. Add text overlays with social message if desired
                    7. Export as final 30-second social awareness film
                    
                    **Message**: "Small acts of kindness create ripples of positive change in our communities"
                    """)
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and fal.ai")

# Instructions in expander
with st.expander("📖 How to use"):
    st.markdown("""
    **Social Awareness Short Film Mode:**
    1. Enter your API key in the sidebar
    2. Click "Generate Video" to start the 6-scene social awareness film
    3. Wait for all 6 scenes to generate (5 seconds each = 30 seconds total)
    4. Download individual scenes
    5. Combine them in video editing software for your final 30-second film
    
    **Story Structure:**
    - **Scene 1**: Urban setting - busy street where people overlook each other
    - **Scene 2**: Problem introduced - elderly woman struggling with groceries
    - **Scene 3**: Awareness - young man notices and feels empathy
    - **Scene 4**: Action - offering help with respectful gesture
    - **Scene 5**: Connection - working together, genuine human kindness
    - **Scene 6**: Ripple effect - others inspired to help, community change
    
    **Methods:**
    - **Blocking**: Waits for completion with real-time updates (recommended)
    - **Queue**: Submit request and poll for status (useful for very long operations)
    
    **Tips for better results:**
    - Each scene flows seamlessly into the next
    - Focus on empathy, action, and positive community impact
    - Be patient - each 5-second video takes several minutes to generate
    - The story shows how small acts of kindness can inspire others
    """)

# Example prompts
with st.expander("💡 Social Awareness Video Scenes"):
    st.markdown("""
    **Scene 1 - Setting the Stage:**
    - "Wide establishing shot of busy city street during afternoon, diverse people walking with purpose, warm natural lighting establishing urban community setting"
    
    **Scene 2 - The Problem:**
    - "Medium close-up of elderly woman struggling with heavy grocery bags at bus stop, looking tired and overwhelmed, other people passing by without noticing"
    
    **Scene 3 - The Awareness:**
    - "Close-up reaction shot of young man in casual clothes noticing the elderly woman's struggle, his expression changing from distracted to concerned and empathetic"
    
    **Scene 4 - Taking Action:**
    - "Medium shot sequence showing the young man approaching and offering help, gentle smile and respectful gesture, elderly woman's grateful surprised expression"
    
    **Scene 5 - Human Connection:**
    - "Heartwarming medium two-shot of them working together, him carrying her bags while they walk and chat, showing genuine human connection and kindness"
    
    **Scene 6 - Ripple Effect:**
    - "Final wide shot pulling back to reveal other people nearby inspired by this act, beginning to help others around them, creating ripple effect of kindness"
    """)

# Troubleshooting section
with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **Common Issues:**
    
    1. **Import Error**: Make sure to install fal-client: `pip install fal-client`
    2. **API Key Error**: Verify your API key is correct and has sufficient credits
    3. **Generation Failed**: Try a simpler or more detailed prompt
    4. **Timeout**: Try again or use queue method for longer operations
    5. **Complex Scenes**: Break down complex prompts into simpler descriptions
    
    **If you're still having issues:**
    - Check your internet connection
    - Verify your fal.ai account status
    - Try with a different or simpler video prompt
    - Reduce complexity of the scene description
    """)