// VOT1 Documentation Interactive Features

document.addEventListener('DOMContentLoaded', function() {
  // Progress bar functionality
  const progressContainer = document.createElement('div');
  progressContainer.className = 'progress-container';
  const progressBar = document.createElement('div');
  progressBar.className = 'progress-bar';
  progressContainer.appendChild(progressBar);
  document.body.appendChild(progressContainer);

  window.addEventListener('scroll', function() {
    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = (winScroll / height) * 100;
    progressBar.style.width = scrolled + '%';
  });

  // Dark/Light mode toggle
  const darkModeToggle = document.createElement('div');
  darkModeToggle.className = 'dark-mode-toggle';
  darkModeToggle.innerHTML = '🌓';
  darkModeToggle.title = 'Toggle Dark/Light Mode';
  document.body.appendChild(darkModeToggle);

  // Check for saved user preference
  const darkMode = localStorage.getItem('darkMode');
  if (darkMode === 'light') {
    document.documentElement.style.setProperty('--background-color', '#f8f9fa');
    document.documentElement.style.setProperty('--surface-color', '#ffffff');
    document.documentElement.style.setProperty('--text-color', '#333333');
    document.documentElement.style.setProperty('--text-muted', '#6c757d');
    document.documentElement.style.setProperty('--code-bg', '#f1f3f5');
    document.documentElement.style.setProperty('--heading-color', '#212529');
    document.documentElement.style.setProperty('--border-color', '#dee2e6');
  }

  darkModeToggle.addEventListener('click', function() {
    const currentMode = localStorage.getItem('darkMode');
    if (currentMode !== 'light') {
      // Switch to light mode
      document.documentElement.style.setProperty('--background-color', '#f8f9fa');
      document.documentElement.style.setProperty('--surface-color', '#ffffff');
      document.documentElement.style.setProperty('--text-color', '#333333');
      document.documentElement.style.setProperty('--text-muted', '#6c757d');
      document.documentElement.style.setProperty('--code-bg', '#f1f3f5');
      document.documentElement.style.setProperty('--heading-color', '#212529');
      document.documentElement.style.setProperty('--border-color', '#dee2e6');
      localStorage.setItem('darkMode', 'light');
    } else {
      // Switch back to dark mode
      document.documentElement.style.setProperty('--background-color', '#0f1114');
      document.documentElement.style.setProperty('--surface-color', '#1a1d21');
      document.documentElement.style.setProperty('--text-color', '#e2e8f0');
      document.documentElement.style.setProperty('--text-muted', '#a0aec0');
      document.documentElement.style.setProperty('--code-bg', '#2d3748');
      document.documentElement.style.setProperty('--heading-color', '#f8f9fa');
      document.documentElement.style.setProperty('--border-color', '#2d3748');
      localStorage.setItem('darkMode', 'dark');
    }
  });

  // Add click events to grid items if they have onclick attributes
  document.querySelectorAll('.grid-item').forEach(item => {
    if (item.getAttribute('onclick')) {
      item.classList.add('clickable');
    }
  });

  // Add smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add copy buttons to code blocks
  document.querySelectorAll('pre').forEach(pre => {
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-button';
    copyButton.textContent = 'Copy';
    
    pre.style.position = 'relative';
    copyButton.style.position = 'absolute';
    copyButton.style.top = '5px';
    copyButton.style.right = '5px';
    copyButton.style.padding = '3px 8px';
    copyButton.style.backgroundColor = 'var(--surface-color)';
    copyButton.style.color = 'var(--text-color)';
    copyButton.style.border = '1px solid var(--border-color)';
    copyButton.style.borderRadius = '4px';
    copyButton.style.fontSize = '12px';
    copyButton.style.cursor = 'pointer';
    copyButton.style.zIndex = '1';
    
    copyButton.addEventListener('click', () => {
      const code = pre.querySelector('code');
      const textToCopy = code ? code.innerText : pre.innerText;
      
      navigator.clipboard.writeText(textToCopy).then(() => {
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
          copyButton.textContent = 'Copy';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy code: ', err);
      });
    });
    
    pre.appendChild(copyButton);
  });

  // Add animated glow effect to important elements
  document.querySelectorAll('.feature-card .feature-icon, h1, .grid-item h2').forEach(element => {
    element.classList.add('highlight');
  });

  // Create dynamic table of contents for long pages
  const headings = document.querySelectorAll('h2');
  if (headings.length > 5) {
    const toc = document.createElement('div');
    toc.className = 'table-of-contents';
    toc.innerHTML = '<h3>Table of Contents</h3><ul></ul>';
    
    const tocList = toc.querySelector('ul');
    headings.forEach((heading, index) => {
      if (!heading.id) {
        heading.id = 'heading-' + index;
      }
      const listItem = document.createElement('li');
      const link = document.createElement('a');
      link.href = '#' + heading.id;
      link.textContent = heading.textContent;
      listItem.appendChild(link);
      tocList.appendChild(listItem);
    });
    
    const firstHeading = headings[0];
    firstHeading.parentNode.insertBefore(toc, firstHeading);
    
    // Style the TOC
    toc.style.backgroundColor = 'var(--surface-color)';
    toc.style.padding = '20px';
    toc.style.borderRadius = '8px';
    toc.style.marginBottom = '30px';
    toc.style.border = '1px solid var(--border-color)';
    toc.style.boxShadow = 'var(--card-shadow)';
  }

  // Add image lazy loading and lightbox effect
  document.querySelectorAll('img').forEach(img => {
    // Add lazy loading
    img.setAttribute('loading', 'lazy');
    
    // Add lightbox effect for larger images
    if (img.width > 300) {
      img.style.cursor = 'pointer';
      img.addEventListener('click', function() {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.style.position = 'fixed';
        lightbox.style.top = '0';
        lightbox.style.left = '0';
        lightbox.style.width = '100%';
        lightbox.style.height = '100%';
        lightbox.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
        lightbox.style.zIndex = '1000';
        lightbox.style.display = 'flex';
        lightbox.style.alignItems = 'center';
        lightbox.style.justifyContent = 'center';
        
        const imgClone = document.createElement('img');
        imgClone.src = img.src;
        imgClone.style.maxWidth = '90%';
        imgClone.style.maxHeight = '90%';
        imgClone.style.objectFit = 'contain';
        imgClone.style.boxShadow = 'none';
        imgClone.style.border = 'none';
        imgClone.style.transform = 'none';
        
        lightbox.appendChild(imgClone);
        document.body.appendChild(lightbox);
        
        lightbox.addEventListener('click', function() {
          document.body.removeChild(lightbox);
        });
      });
    }
  });
}); 