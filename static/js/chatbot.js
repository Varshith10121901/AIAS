/* AIAS Aria Chatbot — Full Lead Qualification */
(function(){
const CFG={
  email:"aiasprivateltd@gmail.com",
  phone:"+91 7022756962",
  calendly:"https://calendly.com/aiasprivateltd",
  supportEmail:"support@aias.in",
  careersEmail:"careers@aias.in",
  partnerEmail:"partners@aias.in"
};

const SERVICES=["Business Website","Mobile App","AI Automation","AI Chatbot","E-commerce Platform","SaaS Dashboard","API Integration","CRM System","Invoice & Billing Tool","Healthcare Portal","Not sure yet"];

const FOLLOWUP={
  "Business Website":"Nice choice! Are we building this website from scratch, or are we redesigning/updating an existing one?",
  "Mobile App":"Awesome. Are you targeting iOS, Android, or do you want a cross-platform app that works on both?",
  "AI Automation":"AI automation can save so much time! What specific business workflows or daily tasks are you hoping to automate?",
  "AI Chatbot":"Chatbots are great for customer service. Where would you like it to live? (e.g., your website, WhatsApp, Slack, etc.)",
  "E-commerce Platform":"E-commerce is exciting. Roughly how many products are we talking about, and are you using Shopify/WooCommerce already?",
  "SaaS Dashboard":"Got it. Do you already have a database or backend set up, or are we starting completely from scratch?",
  "API Integration":"Connecting systems is key. Which software platforms, databases, or APIs need to talk to each other?",
  "CRM System":"A good CRM keeps everything organized. What tool is your team using for customer management today?",
  "Invoice & Billing Tool":"Billing tools save so much headache. Are we replacing a manual invoice process, or building something custom from scratch?",
  "Healthcare Portal":"Healthcare portals need to be super secure. Will this be used by patients, your clinical staff, or both?",
  "Not sure yet":"No worries at all! Just tell me a bit about what challenge you're trying to solve or what your goals are."
};

let step="idle", lead={source:"website",lead_status:"",booking_intent:false,calendly_completed:false}, init=false;

/* ── Auth guard ── */
function loggedIn(){return window.AIAS_CONFIG&&window.AIAS_CONFIG.isLoggedIn===true;}

/* ── Button wiring ── */
document.addEventListener("click",function(e){
  const el=e.target.closest("[data-action='book-call']");
  if(!el)return;
  e.preventDefault();e.stopImmediatePropagation();
  if(!loggedIn()){window.location.href="/signin";return;}
  open();
},true);

/* ── Detect site theme ── */
function isSiteLight(){
  return document.documentElement.classList.contains('light-theme');
}

/* ── Modal ── */
function inject(){
  if(document.getElementById("aria-overlay"))return;
  document.body.insertAdjacentHTML("beforeend",`
<div id="aria-overlay" role="dialog" aria-modal="true" aria-hidden="true">
<div id="aria-modal">
  <div class="ar-head">
    <div class="ar-head-l">
      <div class="ar-av" style="overflow:hidden; background:rgba(12,12,12,0.95);"><img src="/static/images/logo.svg" style="width:100%;height:100%;object-fit:contain;border-radius:50%;" alt="AIAS Logo" /></div>
      <div><div class="ar-nm">Aria · AIAS Assistant</div><div class="ar-st"><span class="ar-dot"></span>Online</div></div>
    </div>
    <div class="ar-head-r">
      <div class="ar-ct">
        <span style="display:flex;align-items:center;justify-content:flex-end;gap:4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.75;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>${CFG.email}</span>
        <span style="display:flex;align-items:center;justify-content:flex-end;gap:4px;margin-top:2px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.75;"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>${CFG.phone}</span>
      </div>
      <button id="aria-close" class="ar-x" aria-label="Close chat">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
  </div>
  <div class="ar-msgs" id="aria-msgs" role="log" aria-live="polite"></div>
  <div class="ar-qr" id="aria-qr"></div>
  <div class="ar-inp-row">
    <input id="aria-inp" class="ar-inp" type="text" placeholder="Type a message…" autocomplete="off" maxlength="400" aria-label="Message"/>
    <button id="aria-send" class="ar-send" type="button" aria-label="Send">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    </button>
  </div>
</div></div>`);
  css();wire();
}

function css(){
  if(document.getElementById("aria-chatbot-css"))return;
  const s=document.createElement("style");
  s.id="aria-chatbot-css";
  s.textContent=`
/* ═══ Overlay ═══ */
#aria-overlay{position:fixed;inset:0;background:rgba(8,8,8,.72);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;visibility:hidden;transition:opacity .28s,visibility .28s;font-family:'DM Sans',-apple-system,sans-serif}
#aria-overlay.on{opacity:1;visibility:visible}

/* ═══ Modal — dark by default ═══ */
#aria-modal{background:#111;border-radius:20px;width:100%;max-width:680px;height:min(720px,calc(100vh - 32px));display:flex;flex-direction:column;overflow:hidden;box-shadow:0 28px 90px rgba(0,0,0,.4);transform:translateY(20px) scale(.97);transition:transform .3s cubic-bezier(.16,1,.3,1),background .4s,box-shadow .4s}
#aria-overlay.on #aria-modal{transform:translateY(0) scale(1)}

/* ═══ Header ═══ */
.ar-head{background:#0A0A0A;padding:15px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;transition:background .4s}
.ar-head-l{display:flex;align-items:center;gap:11px}
.ar-av{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,0.05);color:#0A0A0A;font-weight:800;font-size:16px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.ar-nm{color:#fff;font-size:13.5px;font-weight:600;transition:color .4s}
.ar-st{color:rgba(255,255,255,.45);font-size:10.5px;display:flex;align-items:center;gap:4px;margin-top:2px;transition:color .4s}
.ar-dot{width:6px;height:6px;border-radius:50%;background:#4ade80;animation:ar-p 2s infinite}
@keyframes ar-p{0%,100%{opacity:1}50%{opacity:.3}}
.ar-head-r{display:flex;align-items:center;gap:14px}
.ar-ct{display:flex;flex-direction:column;gap:2px;text-align:right}
.ar-ct span{font-size:10px;color:rgba(255,255,255,.38);transition:color .4s}

/* Close Button */
.ar-x{background:rgba(255,255,255,.08);border:none;color:rgba(255,255,255,.55);cursor:pointer;width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;transition:background .15s,color .15s}
.ar-x:hover{background:rgba(255,255,255,.18);color:#fff}

/* ═══ Messages ═══ */
.ar-msgs{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:10px;scroll-behavior:auto;background:#0a0a0a;transition:background .4s}
.ar-msgs::-webkit-scrollbar{width:3px}
.ar-msgs::-webkit-scrollbar-thumb{background:#333;border-radius:3px}
.ar-msg{display:flex;gap:8px;align-items:flex-end;animation:ar-in .25s ease}
@keyframes ar-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.ar-msg.bot{align-self:flex-start;max-width:84%}
.ar-msg.usr{align-self:flex-end;flex-direction:row-reverse;max-width:84%}
.ar-av2{width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,0.05);color:#0A0A0A;font-size:10px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-bottom:2px}
.ar-b{padding:10.5px 14px;border-radius:14px;font-size:13.5px;line-height:1.6;white-space:pre-wrap;word-break:break-word;transition:background .4s,color .4s,border-color .4s}
.ar-msg.bot .ar-b{background:#1a1a1a;color:#f0f0f0;border:.5px solid #222;border-bottom-left-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.15)}
.ar-msg.usr .ar-b{background:#D4AF37;color:#000;border-bottom-right-radius:4px}

/* Typing indicator */
.ar-typ{display:flex;gap:4px;align-items:center;padding:10px 14px;background:#1a1a1a;border:.5px solid #222;border-radius:14px;border-bottom-left-radius:4px;width:fit-content;box-shadow:0 1px 4px rgba(0,0,0,.15);transition:background .4s,border-color .4s}
.ar-td{width:6px;height:6px;background:#666;border-radius:50%;animation:ar-b2 1.2s infinite}
.ar-td:nth-child(2){animation-delay:.2s}.ar-td:nth-child(3){animation-delay:.4s}
@keyframes ar-b2{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}

/* Quick Reply area */
.ar-qr{padding:9px 16px 10px;display:flex;flex-wrap:wrap;gap:7px;background:#0a0a0a;border-top:.5px solid #222;flex-shrink:0;min-height:50px;transition:background .4s,border-color .4s}
.ar-qb{background:#111;border:.5px solid #D4AF37;color:#D4AF37;font-family:inherit;font-size:12px;font-weight:500;padding:6px 13px;border-radius:18px;cursor:pointer;transition:background .13s,color .13s,transform .1s;white-space:nowrap}
.ar-qb:hover{background:#D4AF37;color:#0A0A0A;transform:translateY(-1px)}

/* Input row */
.ar-inp-row{display:flex;align-items:center;gap:8px;padding:12px 16px;border-top:.5px solid #222;background:#111;flex-shrink:0;transition:background .4s,border-color .4s}
.ar-inp{flex:1;border:.5px solid #333;border-radius:22px;padding:9px 15px;font-family:inherit;font-size:13.5px;outline:none;background:#0a0a0a;transition:border-color .14s,background .4s,color .4s;color:#f0f0f0}
.ar-inp:focus{border-color:#D4AF37;background:#1a1a1a}
.ar-inp::placeholder{color:#666}
.ar-send{width:36px;height:36px;border-radius:50%;background:#D4AF37;border:none;color:#0A0A0A;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .14s,transform .1s}
.ar-send:hover{background:#c9a030}
.ar-send:active{transform:scale(.92)}

/* ═══════════════════════════════════════════
   LIGHT THEME — triggered by site's class
   ═══════════════════════════════════════════ */
.light-theme #aria-modal{background:#fff;box-shadow:0 28px 90px rgba(0,0,0,.12)}
.light-theme .ar-head{background:#f5f5f0}
.light-theme .ar-nm{color:#1a1a1a}
.light-theme .ar-st{color:#888}
.light-theme .ar-ct span{color:#999}
.light-theme .ar-x{background:rgba(0,0,0,.06);color:#888}
.light-theme .ar-x:hover{background:rgba(0,0,0,.12);color:#333}
.light-theme .ar-msgs{background:#f9f9f9}
.light-theme .ar-msgs::-webkit-scrollbar-thumb{background:#ddd}
.light-theme .ar-msg.bot .ar-b{background:#fff;color:#1a1a1a;border-color:#eee;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.light-theme .ar-msg.usr .ar-b{background:#0A0A0A;color:#fff}
.light-theme .ar-typ{background:#fff;border-color:#eee;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.light-theme .ar-td{background:#bbb}
.light-theme .ar-qr{background:#f9f9f9;border-top-color:#efefef}
.light-theme .ar-qb{background:#fff;border-color:#D4AF37;color:#B88912}
.light-theme .ar-qb:hover{background:#D4AF37;color:#0A0A0A}
.light-theme .ar-inp-row{background:#fff;border-top-color:#ebebeb}
.light-theme .ar-inp{background:#f9f9f9;color:#1a1a1a;border-color:#e0e0e0}
.light-theme .ar-inp:focus{border-color:#D4AF37;background:#fff}
.light-theme .ar-inp::placeholder{color:#aaa}
.light-theme .ar-send{background:#0A0A0A;color:#fff}
.light-theme .ar-send:hover{background:#D4AF37}

/* ═══════════════════════════════════════════
   MOBILE — fullscreen takeover
   ═══════════════════════════════════════════ */
@media(max-width:768px){
  #aria-overlay{padding:0;align-items:stretch;justify-content:stretch}
  #aria-modal{border-radius:0;width:100vw;max-width:100vw;height:100vh;height:100dvh;transform:translateY(10px) scale(0.98)}
  #aria-overlay.on #aria-modal{transform:translateY(0) scale(1)}
  .ar-ct{display:none}
  .ar-head{padding:14px 16px}
  .ar-x{width:44px;height:44px;border-radius:10px}
  .ar-x svg{width:22px;height:22px}
  .ar-msgs{padding:16px}
  .ar-qr{padding:10px 14px;gap:6px}
  .ar-inp-row{padding:12px 14px;padding-bottom:calc(12px + env(safe-area-inset-bottom))}
}`;
  document.head.appendChild(s);
}

function wire(){
  document.getElementById("aria-close").addEventListener("click",close);
  document.getElementById("aria-overlay").addEventListener("click",e=>{if(e.target===e.currentTarget)close();});
  document.getElementById("aria-send").addEventListener("click",send);
  document.getElementById("aria-inp").addEventListener("keydown",e=>{if(e.key==="Enter")send();});
  document.getElementById("aria-qr").addEventListener("click",e=>{
    const b=e.target.closest(".ar-qb");if(!b)return;
    handle(b.textContent.trim());
  });
  window.addEventListener("keydown",e=>{if(e.key==="Escape")close();});
}

function open(){
  inject();
  const ov=document.getElementById("aria-overlay");
  ov.classList.add("on");ov.setAttribute("aria-hidden","false");
  document.body.style.overflow="hidden";
  if(!init){init=true;welcome();}
  setTimeout(()=>{document.getElementById("aria-inp")?.focus();},300);
}

function close(){
  const ov=document.getElementById("aria-overlay");if(!ov)return;
  ov.classList.remove("on");ov.setAttribute("aria-hidden","true");
  document.body.style.overflow="";
}

function checkPreviousDetailsOrStart() {
  let prev = null;
  try {
    prev = localStorage.getItem("aria_lead_details");
  } catch(e) {}

  if (prev) {
    try {
      const details = JSON.parse(prev);
      if (details && details.name && details.email) {
        step = "confirm_previous";
        delay(600, () => {
          bot(`Oh, welcome back! I remember you. I've got your details saved from last time:\n\n👤 Name: ${details.name}\n📧 Email: ${details.email}\n🛠️ Service: ${details.service_needed || "TBD"}\n\nShould we use these same details to set up a new call, or would you like to start fresh?`);
          qr(["Yes, use previous details", "No, enter new details"]);
        });
        return;
      }
    } catch(e) {}
  }
  askService();
}

function usePreviousDetails(details) {
  step="done";
  lead.name = details.name;
  lead.email = details.email;
  lead.whatsapp = details.whatsapp;
  lead.service_normalized = details.service_needed;
  lead.budget_range = details.budget_range;
  lead.timeline = details.timeline;
  lead.problem_statement = details.problem_statement;
  lead.booking_intent = true;

  delay(900, () => {
    bot(`Welcome back, ${lead.name}! 🎯\n\nI've submitted a new booking using your previous details:\n🛠️ Service: ${lead.service_normalized || "TBD"}\n💰 Budget: ${lead.budget_range || "TBD"}`);
  });

  setTimeout(() => {
    delay(800, () => {
      bot(`You're all set! ✅\n\nOur team will review your previous project requirements and come prepared. See you soon! 🚀`);
      qr(["Ask another question","Contact team directly"]);
      lead.calendly_completed=true;
    });
    submit();
  }, 2200);
}

/* ── Flow steps ── */
function welcome(){
  step="welcome";
  delay(900,()=>{
    bot(`Hey there! Welcome to AIAS. I'm Aria, and I help our engineering and design team understand exactly what you're looking to build. 😊\n\nWe design and develop high-end websites, mobile apps, SaaS dashboards, and custom AI systems.\n\nAre you here to start a new project, or just looking around for now?`);
    qr(["Yes, I want to build something","Just exploring for now","I want to contact the team"]);
  });
}

function askService(){
  step="service";
  delay(700,()=>{
    bot("Awesome! What kind of project do you have in mind? Pick whatever fits best:");
    qr(SERVICES);
  });
}

function askFollowup(svc){
  step="followup";lead.service_needed=svc;lead.service_normalized=svc;
  delay(700,()=>{
    bot(FOLLOWUP[svc]||"Tell me more about what you need.");
    if (svc === "Mobile App") {
      qr(["iOS", "Android", "Cross-Platform (Both)"]);
    } else if (svc === "Business Website") {
      qr(["Scratch", "Redesign"]);
    } else {
      qr([]);
    }
  });
}

function askBudget(){
  step="budget";
  delay(700,()=>{
    bot("That helps a lot! Just so our architects can suggest the right tech stack — what is your approximate budget for this project?");
    qr(["Under ₹50K","₹50K – ₹2L","₹2L – ₹5L","₹5L+","Let's discuss on the call"]);
  });
}

function askTimeline(){
  step="timeline";
  delay(700,()=>{
    bot("Got it, we build for projects of all sizes! Let's talk about timing. When would you like to get this project kicked off?");
    qr(["As soon as possible","Within 1 month","1–3 months","Just exploring for now"]);
  });
}

function askName(){
  step="name";
  delay(700,()=>{bot("Perfect. I can set up a free 30-minute brainstorming & architecture call with one of our tech leads so we can map out a solution for you.\n\nFirst, what should I call you?");qr([]);});
}

function askEmail(){
  const loggedEmail = window.AIAS_CONFIG && window.AIAS_CONFIG.userEmail;
  if (loggedEmail) {
    step = "confirm_email";
    delay(600,()=>{
      bot(`Wonderful to meet you, ${lead.name}! 👋\n\nI see you are logged in with the email: ${loggedEmail}.\n\nCan we use this email to send your calendar invite and meeting details?`);
      qr([`Yes, use ${loggedEmail}`, "No, enter manually"]);
    });
  } else {
    step = "email";
    delay(600,()=>{
      bot(`Wonderful to meet you, ${lead.name}! 👋\n\nWhat is the best email address to send your calendar invite and meeting details to?`);
      qr([]);
    });
  }
}

function askWhatsApp(){
  step="whatsapp";
  delay(600,()=>{bot("Got it. Lastly, would you like to drop your WhatsApp number? It's completely optional, but we can send you a quick text reminder before our call.");qr(["Skip"]);});
}

function askCallType(){
  step="call_type";
  delay(600,()=>{
    bot("Would you prefer a voice call or a video conference for our session?");
    qr(["Voice Call", "Video Conference"]);
  });
}

function askReview(){
  step="review";
  delay(600,()=>{
    const wa = lead.whatsapp && lead.whatsapp.trim() ? lead.whatsapp : "Not provided";
    const recap = `Please review your details before we finalize your booking:

👤 Name: ${lead.name}
📧 Email: ${lead.email}
📱 WhatsApp: ${wa}
🛠️ Service: ${lead.service_normalized || "TBD"}
📝 Requirements: ${lead.problem_statement || "TBD"}
💰 Budget: ${lead.budget_range || "TBD"}
📅 Timeline: ${lead.timeline || "TBD"}
📞 Call Type: ${lead.call_type || "Voice Call"}`;

    bot(recap);
    qr([
      "Looks good! Confirm call",
      "Edit Name",
      "Edit Email",
      "Edit WhatsApp",
      "Edit Service",
      "Edit Budget",
      "Edit Timeline",
      "Edit Requirements",
      "Edit Call Type"
    ]);
  });
}

function doBooking(){
  step="done";lead.booking_intent=true;
  delay(900,()=>{
    bot(`Awesome, ${lead.name}! 🎯 Confirming your booking and setting up details...`);
  });

  submit(() => {
    delay(1000, () => {
      let msg = `You are all set, ${lead.name}! ✅\n\n`;
      if (lead.call_type === "Video Conference") {
        let dateStr = "in 72 hours";
        if (lead.scheduled_at) {
          try {
            const dt = new Date(lead.scheduled_at);
            dateStr = "for " + dt.toLocaleDateString("en-US", {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
          } catch(e) {}
        }
        msg += `🎥 Video Conference scheduled ${dateStr}!\nPlatform : Zoom\n(The invite link will be sent to your email: ${lead.email})\n\n`;
      } else {
        msg += `📞 Voice Call scheduled! We will contact you on your number: ${lead.whatsapp || lead.email}\n\n`;
      }
      msg += `Our engineering team will review your requirements so we don't waste time on the call. Let's build something awesome! 🚀`;

      bot(msg);
      qr(["Ask another question","Contact team directly"]);
      lead.calendly_completed=true;
    });

    try {
      localStorage.setItem("aria_lead_details", JSON.stringify({
        name: lead.name,
        email: lead.email,
        whatsapp: lead.whatsapp,
        service_needed: lead.service_normalized,
        budget_range: lead.budget_range,
        timeline: lead.timeline,
        problem_statement: lead.problem_statement,
        call_type: lead.call_type
      }));
    } catch(e) {}
  });
}

function showContact(){
  step="idle";
  delay(600,()=>{
    bot(`No problem at all! You can reach our team directly at:\n\n[email_icon] Email: ${CFG.email}\n[phone_icon] WhatsApp / Call: ${CFG.phone}\n\nWe'll get back to you within 24 hours. Or, if you change your mind, we can always schedule a free 30-minute tech call right here!`);
    qr(["Book a Call","Back to main"]);
  });
}

/* ── Router ── */
function handle(txt){
  userMsg(txt);clearQr();
  const lo=txt.toLowerCase();

  // Intent detection — anywhere in flow
  if(/contact|reach|email|phone|whatsapp|call you|speak to/.test(lo)){showContact();return;}
  if(/job|career|hiring|work at|position/.test(lo)){delay(500,()=>{bot(`For career opportunities, please reach out to ${CFG.careersEmail} 👋`);qr(["Book a Call"]);});return;}
  if(/vendor|agency|partner|pitch|outsourc/.test(lo)){delay(500,()=>{bot(`For partnerships, please contact ${CFG.partnerEmail}.`);qr(["Book a Call"]);});return;}
  if(/support|bug|fix|issue|existing project/.test(lo)&&step!=="followup"){delay(500,()=>{bot(`For existing project support, please contact ${CFG.supportEmail}.\n\nI can help with new project inquiries and calls.`);qr(["New project","Book a Call"]);});return;}
  if(/are you ai|are you a bot|are you human|who are you/.test(lo)){delay(400,()=>{bot("Yes — I'm AIAS's assistant (Aria), here to make sure your call is actually useful. 😊");qr([]);setTimeout(()=>routeStep(lo,txt),600);});return;}
  if(/just brows|no project|maybe later|not now/.test(lo)){delay(500,()=>{bot("No problem! Want a quick overview of what AIAS usually builds?");qr(["Yes, show me","Book a call instead"]);step="exploring";});return;}
  if(/pric|how much|cost|rate|charge/.test(lo)&&step!=="budget"){delay(500,()=>{bot("Pricing depends on scope, features, and timeline — the call helps us give you an exact estimate.\n\nWant to book a quick 30-min discussion?");qr(["Yes, book a call","Tell me more first"]);});return;}

  // Booking intent detection
  if (/book|call|schedule|meeting|appoint|conf|session|video|voice/.test(lo)) {
    const captureSteps = ["confirm_previous", "service", "followup", "budget", "timeline", "name", "confirm_email", "email", "whatsapp", "call_type", "review", "edit_name", "edit_email", "edit_whatsapp", "edit_service", "edit_budget", "edit_timeline", "edit_problem", "edit_call_type"];
    if (!captureSteps.includes(step)) {
      checkPreviousDetailsOrStart();
      return;
    }
  }

  routeStep(lo,txt);
}

function routeStep(lo,txt){
  switch(step){
    case"welcome":
      if(/build|project|need|want|looking/.test(lo))checkPreviousDetailsOrStart();
      else if(/explor|browse|overview|show me/.test(lo)){delay(600,()=>{bot("AIAS builds websites, mobile apps, AI automations, SaaS dashboards, e-commerce platforms, chatbots, CRMs, and more.\n\nWhat sounds relevant to your situation?");qr(SERVICES);step="service";});}
      else checkPreviousDetailsOrStart();
      break;

    case"confirm_previous":
      if(lo.includes("yes") || lo.includes("use prev") || lo.includes("sure") || lo.includes("ok")){
        let prev = null;
        try { prev = localStorage.getItem("aria_lead_details"); } catch(e) {}
        if(prev){
          try {
            const details = JSON.parse(prev);
            usePreviousDetails(details);
            break;
          } catch(e) {}
        }
        askService();
      } else {
        askService();
      }
      break;

    case"exploring":
      checkPreviousDetailsOrStart();break;

    case"service":{
      const match=SERVICES.find(s=>lo.includes(s.toLowerCase()));
      askFollowup(match||txt);break;}

    case"followup":
      lead.problem_statement=txt;
      askBudget();break;

    case"budget":
      lead.budget_range=txt;
      if(/low|under|50k|no budget|small/.test(lo)){delay(600,()=>{bot("Got it, we build for projects of all sizes! Let's talk about timing. When would you like to get this project kicked off?");qr(["As soon as possible","Within 1 month","1–3 months","Just exploring"]);step="timeline";});}
      else askTimeline();
      break;

    case"timeline":
      lead.timeline=txt;
      if(/explor|not sure|later/.test(lo)){delay(600,()=>{bot("That's fine! I'll still capture your requirement so the team can reach out when you're ready.\n\nCan I get your name?");step="name";qr([]);});}
      else askName();
      break;

    case"name":
      if(txt.length<2){delay(400,()=>{bot("Could you share your name?");});return;}
      lead.name=txt;askEmail();break;

    case"confirm_email":{
      const loggedEmail = window.AIAS_CONFIG && window.AIAS_CONFIG.userEmail;
      if (lo.includes("yes") || lo.includes("use") || lo.includes("sure") || lo.includes("ok")) {
        lead.email = loggedEmail;
        askWhatsApp();
      } else {
        step = "email";
        delay(400, () => {
          bot("No problem! Please type the email address you'd prefer to use:");
          qr([]);
        });
      }
      break;
    }

    case"email":
      if(!txt.includes("@")){delay(400,()=>{bot("Please enter a valid email address.");});return;}
      lead.email=txt;askWhatsApp();break;

    case"whatsapp":
      lead.whatsapp=txt==="Skip"?"":txt;
      askCallType();
      break;

    case"call_type":
      lead.call_type=txt;
      askReview();
      break;

    case"review":
      if(lo.includes("looks good") || lo.includes("confirm")){
        doBooking();
      }
      else if(lo.includes("edit name")){
        step="edit_name";
        delay(400,()=>{bot("What is your correct name?");qr([]);});
      }
      else if(lo.includes("edit email")){
        step="edit_email";
        delay(400,()=>{bot("What is your correct email address?");qr([]);});
      }
      else if(lo.includes("edit whatsapp")){
        step="edit_whatsapp";
        delay(400,()=>{bot("What is your correct WhatsApp number?");qr(["Skip"]);});
      }
      else if(lo.includes("edit service")){
        step="edit_service";
        delay(400,()=>{bot("What service are you looking to build?");qr(SERVICES);});
      }
      else if(lo.includes("edit budget")){
        step="edit_budget";
        delay(400,()=>{bot("What is your budget range?");qr(["Under ₹50K","₹50K – ₹2L","₹2L – ₹5L","₹5L+","Let's discuss on the call"]);});
      }
      else if(lo.includes("edit timeline")){
        step="edit_timeline";
        delay(400,()=>{bot("What is your timeline?");qr(["As soon as possible","Within 1 month","1–3 months","Just exploring"]);});
      }
      else if(lo.includes("edit requirement") || lo.includes("edit problem")){
        step="edit_problem";
        delay(400,()=>{
          bot("Tell me a bit more about your requirements or what you want to build:");
          if (lead.service_normalized === "Mobile App") {
            qr(["iOS", "Android", "Cross-Platform (Both)"]);
          } else if (lead.service_normalized === "Business Website") {
            qr(["Scratch", "Redesign"]);
          } else {
            qr([]);
          }
        });
      }
      else if(lo.includes("edit call type")){
        step="edit_call_type";
        delay(400,()=>{bot("Would you prefer a voice call or a video conference?");qr(["Voice Call", "Video Conference"]);});
      }
      else {
        delay(400,()=>{
          bot("Please select 'Looks good! Confirm call' or choose a field to edit below.");
          askReview();
        });
      }
      break;

    case"edit_name":
      if(txt.length<2){delay(400,()=>{bot("Could you share your correct name?");});return;}
      lead.name=txt;
      delay(400,()=>{bot(`Updated! Your name is now: ${lead.name}`); askReview();});
      break;

    case"edit_email":
      if(!txt.includes("@")){delay(400,()=>{bot("Please enter a valid email address.");});return;}
      lead.email=txt;
      delay(400,()=>{bot(`Updated! Your email is now: ${lead.email}`); askReview();});
      break;

    case"edit_whatsapp":
      lead.whatsapp=txt==="Skip"?"":txt;
      delay(400,()=>{bot(`Updated! Your WhatsApp number is now: ${lead.whatsapp || "Not provided"}`); askReview();});
      break;

    case"edit_service":
      lead.service_needed=txt;
      lead.service_normalized=txt;
      delay(400,()=>{bot(`Updated! Chosen service is now: ${lead.service_normalized}`); askReview();});
      break;

    case"edit_budget":
      lead.budget_range=txt;
      delay(400,()=>{bot(`Updated! Budget range is now: ${lead.budget_range}`); askReview();});
      break;

    case"edit_timeline":
      lead.timeline=txt;
      delay(400,()=>{bot(`Updated! Timeline is now: ${lead.timeline}`); askReview();});
      break;

    case"edit_problem":
      lead.problem_statement=txt;
      delay(400,()=>{bot(`Updated! Project requirements updated.`); askReview();});
      break;

    case"edit_call_type":
      lead.call_type=txt;
      delay(400,()=>{bot(`Updated! Selected call type is now: ${lead.call_type}`); askReview();});
      break;

    case"done":
      if(/book|call|another|new project/.test(lo)){step="idle";checkPreviousDetailsOrStart();}
      else if(/contact|team/.test(lo)){showContact();}
      else{delay(500,()=>{bot("Feel free to ask me anything about AIAS!");qr(["Book a Call","Contact team","What can AIAS build?"]);});}
      break;

    default:
      delay(600,()=>{bot("I'm here to help! You can book a free 30-min call, ask about our services, or get our contact details.");qr(["Book a Call","Contact team","What can AIAS build?"]);});
  }
}

/* ── Backend ── */
function submit(cb){
  fetch("/book-call",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      name: lead.name || "",
      email: lead.email || "",
      whatsapp: lead.whatsapp || "",
      service_needed: lead.service_normalized || "",
      budget_range: lead.budget_range || "",
      timeline: lead.timeline || "",
      problem_statement: lead.problem_statement || "",
      call_type: lead.call_type || "Voice Call",
      source: lead.source || "website",
      lead_status: lead.booking_intent ? "booked" : "lead",
      timestamp: new Date().toISOString()
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.zoom_meeting_link) {
      lead.zoom_meeting_link = data.zoom_meeting_link;
    }
    if (data.scheduled_at) {
      lead.scheduled_at = data.scheduled_at;
    }
    if (cb) cb();
  })
  .catch(()=>{
    if (cb) cb();
  });
}

/* ── UI helpers ── */
function bot(txt, cb){
  const m=document.getElementById("aria-msgs");
  const d=document.createElement("div");d.className="ar-msg bot";

  const av = document.createElement("div");
  av.className = "ar-av2";
  av.style.overflow = "hidden";
  av.innerHTML = `<img src="/static/images/logo.svg" style="width:100%;height:100%;object-fit:contain;border-radius:50%;" />`;

  const b = document.createElement("div");
  b.className = "ar-b";
  b.style.opacity = "0";
  b.style.transform = "translateY(6px)";
  b.style.transition = "opacity 0.2s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)";

  d.appendChild(av);
  d.appendChild(b);
  m.appendChild(d);
  scroll();

  setTimeout(() => {
    b.style.opacity = "1";
    b.style.transform = "translateY(0)";
  }, 20);

  if (!txt) {
    if (cb) cb();
    return;
  }

  // Type 2 characters at a time every 10ms for a super fluid, fast stream
  let i = 0;
  let currentText = "";

  function typeChar() {
    if (i < txt.length) {
      currentText += txt.slice(i, i + 2);
      b.innerHTML = fmt(currentText);
      i += 2;
      scroll();
      setTimeout(typeChar, 10);
    } else {
      b.innerHTML = fmt(txt);
      scroll();
      if (cb) cb();
    }
  }

  typeChar();
}

function userMsg(txt){
  const m=document.getElementById("aria-msgs");
  const d=document.createElement("div");d.className="ar-msg usr";
  d.innerHTML=`<div class="ar-b" style="opacity: 0; transform: translateY(6px); transition: opacity 0.2s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);">${esc(txt)}</div>`;
  m.appendChild(d);
  scroll();
  setTimeout(() => {
    const b = d.querySelector('.ar-b');
    if (b) {
      b.style.opacity = "1";
      b.style.transform = "translateY(0)";
    }
  }, 20);
}

function delay(ms,cb){
  const m=document.getElementById("aria-msgs");
  const r=document.createElement("div");r.className="ar-msg bot";r.id="aria-typ";
  r.innerHTML=`<div class="ar-av2" style="overflow:hidden;"><img src="/static/images/logo.svg" style="width:100%;height:100%;object-fit:contain;border-radius:50%;" /></div><div class="ar-typ"><span class="ar-td"></span><span class="ar-td"></span><span class="ar-td"></span></div>`;
  m.appendChild(r);scroll();
  setTimeout(()=>{document.getElementById("aria-typ")?.remove();cb();},ms);
}

function qr(items){
  const c=document.getElementById("aria-qr");if(!c)return;
  c.innerHTML=items.map(r=>`<button class="ar-qb" type="button">${esc(r)}</button>`).join("");
}

function clearQr(){const c=document.getElementById("aria-qr");if(c)c.innerHTML="";}
function scroll(){
  const m=document.getElementById("aria-msgs");
  if(m) {
    m.scrollTop = m.scrollHeight;
  }
}
function fmt(t){
  let s = esc(t).replace(/\n/g,"<br>");
  s = s.replace(/\[email_icon\]/g, `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:4px;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`);
  s = s.replace(/\[phone_icon\]/g, `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:4px;"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>`);
  return s;
}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function send(){
  const i=document.getElementById("aria-inp");
  const t=i.value.trim();if(!t)return;
  i.value="";handle(t);
}
})();
