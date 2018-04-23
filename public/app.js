(function() {
  // Get elements
  const txtEmail = document.getElementById('txtEmail');
  const txtPassword = document.getElementById('txtPassword');
  const btnLogin = document.getElementById('btnLogin');
  const btnSignUp = document.getElementById('btnSignUp');
  const btnLogout = document.getElementById('btnLogout');

  // Add login event
  btnLogin.addEventListener('click', e => {
    // Get email and pass
    const email = txtEmail.value;
    const pass = txtPassword.value;
    const auth = firebase.auth();
    // Sign in
    const promise = auth.signInWithEmailAndPassword(email, pass);
    promise.catch(e => console.log(e.message));
  });

  // Log out
  btnLogout.addEventListener('click', e => {
    firebase.auth().signOut();
  });

  // Add Signup event
  btnSignUp.addEventListener('click', e => {
    // TODO: chech for real email
    const email = txtEmail.value;
    const pass = txtPassword.value;
    const auth = firebase.auth();
    // Sign up
    const promise = auth.createUserWithEmailAndPassword(email, pass);
    promise.catch(e => console.log(e.message));
  });
  // Add a realtime listener
  firebase.auth().onAuthStateChanged(firebaseUser => {
    if (firebaseUser) {
        console.log(firebaseUser);
        //btnLogout.classList.remove('hide');
        btnLogout.style.visibility='visible';
    } else {
      console.log('not logged in');
      btnLogout.style.visibility='hidden';
    }
  });
}());

function twitterSignIn() {
  var provider = new firebase.auth.TwitterAuthProvider();

  firebase.auth().signInWithPopup(provider).then(function(result) {
    // This gives you a the Twitter OAuth 1.0 Access Token and Secret.
    // You can use these server side with your app's credentials to access the Twitter API.
    var token = result.credential.accessToken;
    var secret = result.credential.secret;
    // The signed-in user info.
    var user = result.user;
    console.log(token);
    console.log(secret);
    console.log(user);
    // ...
  }).catch(function(error) {
    // Handle Errors here.
    var errorCode = error.code;
    var errorMessage = error.message;
    // The email of the user's account used.
    var email = error.email;
    // The firebase.auth.AuthCredential type that was used.
    var credential = error.credential;
    // ...
  });
}

function googleSignIn() {
  var provider = new firebase.auth.GoogleAuthProvider();
  // Sign in with Google Account
  firebase.auth().signInWithPopup(provider).then(function(result) {
    // This gives you a Google Access Token. You can use it to access the Google API.
    var token = result.credential.accessToken;
    // The signed-in user info.
    var user = result.user;
    console.log("sign in");
    // ...
  }).catch(function(error) {
    // Handle Errors here.
    var errorCode = error.code;
    var errorMessage = error.message;
    // The email of the user's account used.
    var email = error.email;
    // The firebase.auth.AuthCredential type that was used.
    var credential = error.credential;
    // ...
  });
}
