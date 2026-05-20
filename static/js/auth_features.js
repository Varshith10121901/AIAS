document.addEventListener('DOMContentLoaded', () => {
    const featureTexts = [
        [
            "Intelligent Workflow Automation", "AI-Powered Decision Making", "Smart Process Optimization", 
            "Autonomous AI Systems", "AI-Driven Productivity", "Predictive AI Insights", 
            "Adaptive AI Infrastructure", "Automated Business Operations", "Human-Centered Intelligence",
            "Precision Meets Intelligence", "Technology That Moves Faster"
        ],
        [
            "Built for High-Growth Teams", "Scalable Business Intelligence", "Faster Operational Execution", 
            "Smarter Business Decisions", "Growth Through Intelligence", "Accelerated Team Performance", 
            "Built for Modern Businesses", "Enterprise Operational Excellence", "Powering Smarter Businesses",
            "Reduce Complexity at Scale", "Future-Ready Infrastructure"
        ],
        [
            "Enterprise-Grade Security", "Privacy-First Architecture", "Reliable & Secure Systems", 
            "Trusted Infrastructure", "Built with Compliance in Mind", "High Availability Systems", 
            "Secure Cloud Environment", "Data Protection by Design", "Reliable AI Operations", "Performance You Can Trust"
        ],
        [
            "Cloud-Native Architecture", "Seamless Platform Integration", "Enterprise SaaS Infrastructure", 
            "Always-On Performance", "Real-Time Operational Visibility", "API-First Ecosystem", 
            "Scalable Digital Infrastructure", "Designed for Performance", "Built for Scale",
            "Designed for the Future", "Engineered for Ambition", "Built to Think Bigger", 
            "The Future of Intelligent Work", "Innovation at Enterprise Scale", "Built for Visionaries", "Intelligence Without Limits"
        ]
    ];

    const featureItems = document.querySelectorAll('.feature-item span');

    // Colors and state
    const colors = ['var(--text-primary)', 'var(--accent-primary)']; // Text, Gold
    
    // Initial setup for items
    featureItems.forEach((item, index) => {
        item.style.transition = 'none';
        item.style.display = 'inline-block';
        
        // Start with alternating colors in the list for better visual balance
        // Item 0: Black, Item 1: Gold, Item 2: Black, Item 3: Gold
        const startColorIndex = index % 2;
        item.style.color = colors[startColorIndex];
        item._currentColorIndex = startColorIndex;
    });

    setInterval(() => {
        // Update ALL items together
        featureItems.forEach((item, index) => {
            if (!item) return;

            // Remove class to reset animation
            item.classList.remove('animate__rubberBand');
            
            // Force reflow to restart animation
            void item.offsetWidth;
            
            // Step 2: Change text immediately since rubberBand is an attention seeker
            const textArray = featureTexts[index];
            const randomText = textArray[Math.floor(Math.random() * textArray.length)];
            item.textContent = randomText;
            
            // Step 3: Alternate color
            const nextColorIndex = (item._currentColorIndex + 1) % 2;
            item.style.color = colors[nextColorIndex];
            item._currentColorIndex = nextColorIndex;

            // Step 4: Add animation
            item.classList.add('animate__rubberBand');
        });

    }, 4000); // Rotate everything every 4 seconds
});
