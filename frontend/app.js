// Use the global supabase object provided by the UMD CDN script
const { createClient } = supabase;

// Replace with your actual Supabase URL and ANON Key from the backend .env
const supabaseUrl = 'https://qgdcjihqphldvfxdkbog.supabase.co';
const supabaseKey = 'sb_publishable_mkRiOgVLOH1vb8RtI5Kv2g_bHQKOOqo';
const supabaseClient = createClient(supabaseUrl, supabaseKey);

const API_BASE_URL = 'https://infinite-weaver-api-1.onrender.com';

document.addEventListener('DOMContentLoaded', () => {
    
    // --- AKINATOR STATE ---
    let currentWorldBible = {};
    let currentInterviewHistory = [];
    
    // --- HOME PAGE LOGIC (Generate Story) ---
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const promptInput = document.getElementById('promptInput');
            const loadingStatus = document.getElementById('loadingStatus');
            const promptText = promptInput.value.trim();

            if (!promptText) {
                alert("Please describe a hero, setting, or conflict first!");
                return;
            }

            // UI State
            generateBtn.disabled = true;
            generateBtn.style.opacity = '0.5';
            loadingStatus.classList.remove('hidden');
            
            // Render Cold Start UX
            const loadingText = loadingStatus.querySelector('span:nth-child(2)');
            const originalText = loadingText.textContent;
            
            const coldStartTimeout = setTimeout(() => {
                loadingText.textContent = "Waking up the Citadel (this may take up to 50s)...";
                loadingText.classList.add("text-secondary", "animate-pulse");
            }, 5000);

            try {
                const response = await fetch(`${API_BASE_URL}/api/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        prompt: promptText,
                        world_bible: currentWorldBible,
                        interview_history: currentInterviewHistory
                    })
                });

                if (!response.ok) {
                    throw new Error("Failed to generate story");
                }

                const result = await response.json();
                console.log("Generation complete:", result);
                
                // Update Local State
                if (result.world_bible) currentWorldBible = result.world_bible;
                if (result.interview_history) currentInterviewHistory = result.interview_history;
                
                if (!result.story_draft && result.follow_up_question) {
                    // Inject Chat UI
                    appendChatMessage('user', promptText);
                    appendChatMessage('ai', result.follow_up_question);
                    
                    // Update UI for next turn
                    promptInput.value = '';
                    promptInput.placeholder = 'Answer the Citadel...';
                    document.getElementById('forgeTitle').textContent = 'The Citadel Asks...';
                    document.getElementById('btnText').textContent = 'Reply';
                    
                    return; // Do not redirect yet
                } else if (!result.story_draft) {
                    throw new Error("No story was generated.");
                }
                
                // Redirect to stories feed to see the new creation
                window.location.href = 'stories.html';
                
            } catch (error) {
                console.error(error);
                alert("The forge encountered an error. Please try again.");
            } finally {
                clearTimeout(coldStartTimeout);
                loadingText.textContent = originalText;
                loadingText.classList.remove("text-secondary", "animate-pulse");
                generateBtn.disabled = false;
                generateBtn.style.opacity = '1';
                loadingStatus.classList.add('hidden');
            }
        });
    }

    // --- STORIES PAGE LOGIC (Fetch Feed) ---
    const storyFeed = document.getElementById('storyFeed');
    if (storyFeed) {
        loadStories();
    }
});

function appendChatMessage(role, text) {
    const chatHistory = document.getElementById('chatHistory');
    if (!chatHistory) return;
    
    chatHistory.classList.remove('hidden');
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `p-3 rounded-lg text-sm w-[90%] ${role === 'user' ? 'bg-primary/20 border border-primary/30 text-on-surface self-end ml-auto' : 'bg-surface-variant border border-outline text-on-surface self-start'}`;
    
    const label = document.createElement('div');
    label.className = `text-xs font-bold mb-1 tracking-wider uppercase ${role === 'user' ? 'text-primary' : 'text-secondary'}`;
    label.textContent = role === 'user' ? 'You' : 'The Citadel';
    
    const content = document.createElement('div');
    content.textContent = text;
    
    msgDiv.appendChild(label);
    msgDiv.appendChild(content);
    chatHistory.appendChild(msgDiv);
    
    // Auto-scroll
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function loadStories() {
    const feedContainer = document.getElementById('storyFeed');
    const loadingMsg = document.getElementById('loadingFeedStatus');
    const template = document.getElementById('storyCardTemplate');

    try {
        // Fetch stories from Supabase, ordered by newest first
        const { data: stories, error } = await supabaseClient
            .from('stories')
            .select('*')
            .order('created_at', { ascending: false });

        if (error) throw error;

        // Hide loading
        if (loadingMsg) loadingMsg.style.display = 'none';

        if (!stories || stories.length === 0) {
            feedContainer.innerHTML += `<p class="text-on-surface-variant text-center mt-8">The archives are empty. Forge a new story!</p>`;
            return;
        }

        // Render each story
        stories.forEach(story => {
            const clone = template.content.cloneNode(true);
            
            // Populate Text
            clone.querySelector('.story-title').textContent = story.prompt || "An Epic Tale";
            clone.querySelector('.story-content').textContent = story.story_text || "No story content found.";
            
            // Format Date if available
            const dateEl = clone.querySelector('.story-date');
            if (dateEl && story.created_at) {
                const date = new Date(story.created_at);
                dateEl.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            }

            // Populate Comic Image
            const comicImg = clone.querySelector('.story-comic');
            if (comicImg) {
                comicImg.src = story.comic_url || 'https://placeholder.pics/svg/400?text=No+Comic';
            }

            // Populate Meme Image
            const memeContainer = clone.querySelector('.meme-container');
            const memeImg = clone.querySelector('.story-meme');
            
            if (story.meme_url) {
                memeImg.src = story.meme_url;
            } else {
                if (memeContainer) memeContainer.style.display = 'none';
            }

            feedContainer.appendChild(clone);
        });

    } catch (error) {
        console.error("Error fetching stories:", error);
        loadingMsg.innerHTML = "Failed to load chronicles.";
    }
}
