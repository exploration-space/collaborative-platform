import PubSubChannel from './src/utilities/pubsub.js';
import AnnotatorWebSocket from './src/utilities/websocket.js';
import DocumentView from './src/document_view.js';
import PanelView from './src/panel.js';
import Annotator from './src/annotator.js';
import HistoryView from './src/history.js';
import CertaintyList from './src/cert_list.js';
import RecipesPlugin from './src/recipes_plugin.js';
import {Popup, Tooltips} from './src/tooltips.js';
import Alert from './src/utilities/alert.js';
import UISetup from './src/ui.js';

// Load all components
const websocket = AnnotatorWebSocket();
const channel = PubSubChannel.create();

const recipes_plugin = RecipesPlugin({channel});
const uisetup = UISetup({channel});
const document_view = DocumentView({channel});
const panel_view = PanelView({channel});
const annotator = Annotator({channel});
const history_view = HistoryView({channel});
const cert_list = CertaintyList({channel});
const popup = Popup({channel});
const tooltips = Tooltips({channel});

// Create suscriber for sending messages using
// the websocket
const sub = {};
channel.addToChannel(sub);
sub.subscribe('recipesWebsocket/send', json=>websocket.send(json));
sub.subscribe('document/render', selection=>console.info('Document rendered.'));

// Publish websocket updates
websocket.addCallback('onload', file=>sub.publish('document/load', file));
websocket.addCallback('onload', ()=>Alert.alert('success','Document successfully loaded.'));
//AnnotatorWebSocket.addCallback('onload', file=>console.log(file));
websocket.addCallback('onreload', file=>sub.publish('document/load', file));
websocket.addCallback('onreload', ()=>Alert.alert('success','Changes successfully loaded.'));

// Create websocket
websocket.create();