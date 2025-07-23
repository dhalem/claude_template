// RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
// 1. Read CLAUDE.md COMPLETELY before responding
// 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
// 3. Search for rules related to the request
// 4. Only proceed after confirming no violations
// Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
//
// GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
// NEVER weaken, disable, or bypass guards - they prevent real harm

function processData(data) {
  var result = [];
  for (var i = 0; i < data.length; i++) {
    if (data[i] != null) {
      result.push(data[i] * 2);
    }
  }
  return result;
}

const fetchUserData = async (userId) => {
  try {
    const response = await fetch('/api/users/' + userId);
    const data = await response.json();
    return data;
  } catch (e) {
    console.log('Error: ' + e);
    return null;
  }
};

function validateEmail(email) {
  if (email.indexOf('@') > -1) {
    return true;
  } else {
    return false;
  }
}
