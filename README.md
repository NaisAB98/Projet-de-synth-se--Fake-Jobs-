PARTIE INTERFACE UTILISATEUR ET API :

Installation des dépendances pour le site web :

curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install nodejs -y
node -v
npm -v
npx create-react-app fake-news-checker --template typescript
cd fake-news-checker
npm install axios
npm audit fix --force

sudo apt install python3-venv
python3 -m venv myprojectenv
source myprojectenv/bin/activate
pip install flask-cors

Paramétrage : 

dans package.json, remplacer 

  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  
par 

  "scripts": {
  "start": "export NODE_OPTIONS=--openssl-legacy-provider && react-scripts start",
  "build": "export NODE_OPTIONS=--openssl-legacy-provider && react-scripts build",
  "test": "export NODE_OPTIONS=--openssl-legacy-provider && react-scripts test",
  "eject": "react-scripts eject"
  },

ATTENTION : Il manque encore des dépendances à installer, exécuter le programme sans devrait envoyer une erreur disant quelles dépendances sont manquantes
Bien penser à faire source myprojectenv/bin/activate avant d'installer les dépendances ou d'exécuter le code, sinon ça peut ne pas fonctionner
  

Exécution :
dans le src du projet react :
-on ouvre 2 terminaux :
1er terminal : source myprojectenv/bin/activate
python3 app.py
2nd terminal : npm start
