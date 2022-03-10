import * as d3 from 'd3';
import React, { useState, useEffect, useContext } from 'react';
import ReactDOM from 'react-dom';
import ReactGA from 'react-ga';
import {
    BrowserRouter,
    Switch,
    Route,
    useHistory,
    useLocation,
    useRouteMatch
 } from "react-router-dom";

import 'tachyons';
import './app.scss';

import Navbar from './components/navbar.jsx';
import Footer from './components/footer.jsx';
import settings from './settings/settings.js';
import CellLineTable from './components/cellLineTable.jsx';

import Home from './views/home/Home.jsx';
import Dashboard from './views/dashboard/Dashboard';
import SearchResults from './views/searchResults/searchResults.jsx';
import TargetProfile from './views/targetProfile/targetProfile.jsx';
import InteractorProfile from './views/interactorProfile/interactorProfile.jsx';
import Gallery from './views/gallery/Gallery.jsx';
import UMAPContainer from './views/umap/umapContainer.jsx';
import About from './views/about/About.jsx';
import Help from './views/help/Help.jsx';
import Privacy from './views/privacy/Privacy.jsx';
import Contact from './views/contact/Contact.jsx';
import Jobs from './views/jobs/Jobs.jsx';
import Download from './views/download/Download.jsx';


function useCellLineId () {
    // manages the current cellLineId, which is both an app-level piece of state
    // and is included in the URL of the 'target', 'fovs', and 'annotations' pages

    const debug = false;
    let history = useHistory();
    let match = useRouteMatch('/:page');
    const [cellLineId, setCellLineId] = useState(null);

    const onSetCellLineId = (newId, push = true) => {

        if (debug) console.log('onSetCellLineId called');

        // target-specific pages 
        // (i.e. paths of the form `/:page/:cellLineId` that render a TargetProfile component)
        const targetSpecificPages = ['target', 'fovs', 'annotations'];

        // if the newId is `undefined`, then newCellLineId is NaN
        newId = String(newId);
        let newCellLineId = newId.startsWith('CID') ? parseInt(newId.slice(3)) : parseInt(newId);

        let page = match?.params.page;

        // if both the new and old ids are NaN
        // TODO: what scenarios does this correspond to?
        if (!newCellLineId && !cellLineId) return;

        // check that the new cellLineId is not the same as the current cellLineId
        // to prevent an infinite loop in which the call to history.push or history.replace below
        // triggers the `props.match`-dependent effect in the TargetProfile component,
        // which in turn calls this function (onSetCellLineId) again
        if (targetSpecificPages.includes(page) && (newCellLineId===cellLineId)) return;

        // if we are on a target-specific page without a new cellLineId, retain the current cellLineId 
        // (occurs when the user clicks on the navbar links to the /fovs and /annotations pages from the target page,
        // via the props.match-dependent effect in the TargetProfile component)
        if (targetSpecificPages.includes(page) && !newCellLineId) newCellLineId = cellLineId;

        // if we are on the home page, redirect to the target page
        page = page ? page : 'target';

        // if we are not on a target-specific page, redirect to the target page
        page = !targetSpecificPages.includes(page) ? 'target' : page;

        const newUrl = `/${page}/CID${newCellLineId.toString().padStart(6, '0')}${history.location.search}`;

        if (push) {
            history.push(newUrl);
            if (debug) console.log(`Pushing new URL to history: ${newUrl}`);
        } else {
            history.replace(newUrl);
         }

         if (debug) console.log(`cellLineId changed from ${cellLineId} to ${newCellLineId}`);
        setCellLineId(newCellLineId);
    }
    return [cellLineId, onSetCellLineId];
}


function useGeneNameSearch (setCellLineId) {
    // returns a callback to execute when the user hits enter in a target search textbox,
    // which needs to both update the search query if it has changed and also call setCellLineId
    // even if the search has not changed, in order to run the page redirection in setCellLineId
    // (e.g., to redirect from /gallery to /profile even if the search, and cellLineId, is unchanged)

    let history = useHistory();
    const [doSearch, setDoSearch] = useState(true);
    const [searchResultsFound, setSearchResultsFound] = useState(true);
    const [geneName, setGeneName] = useState();
    const modeContext = useContext(settings.ModeContext);

    // retrieve a cellLineId from the target name query
    // HACK: if there's more than one matching ensg_id or oc_id, we arbitrarily pick one
    useEffect(() => {

        if (!geneName || !doSearch) return;

        // hack: remove slashes, which are used in some cytoscape node labels
        const sanitizedGeneName = geneName.split('/')[0]

        const url = `
            ${settings.apiUrl}/search/${sanitizedGeneName}?publication_ready=${modeContext==='public'}
        `;
        d3.json(url).then(result => {
            if (result.oc_ids) {
                setCellLineId(result.oc_ids[0].replace('OPCT', ''));
            } else if (result.ensg_ids) {
                history.push(`/gene/${result.ensg_ids[0]}${history.location.search}`);
            } else {
                setSearchResultsFound(false);
                return;
            }
        });
    }, [geneName]);

    const handleGeneNameSearch = (query) => { setGeneName(query); setDoSearch(true); };
    return handleGeneNameSearch;
}


function useGoogleAnalytics () {
    const location = useLocation();
    ReactGA.initialize(settings.gaTrackingId, {debug: false});
    useEffect(() => {
        ReactGA.pageview(`${location.pathname}${location.search}`);
    }, [location]);
}


function App() {

    useGoogleAnalytics();
    const modeContext = useContext(settings.ModeContext);    
    const [cellLineId, setCellLineId] = useCellLineId();
    const handleGeneNameSearch = useGeneNameSearch(setCellLineId);

    // handle the back button
    const history = useHistory();
    const match = useRouteMatch('/:mode/:cellLineId');
    useEffect(() => {
        return () => {
            if (history.action === "POP" && match?.isExact) {
                console.log(`back button handler with ${match.params.cellLineId}`);
            }
        }
    }, []);

    const publicRoutes = [
        <Route
            exact
            key='targets'
            path={['/target', '/targets']}
            render={props => (
                <CellLineTable
                    {...props}
                    cellLineId={cellLineId}
                    setCellLineId={setCellLineId}
                />
            )}
        />,
        <Route
            key='target'
            path='/target/:cellLineId'
            render={props => (
                <TargetProfile
                    {...props}
                    cellLineId={cellLineId}
                    setCellLineId={setCellLineId}
                    handleGeneNameSearch={handleGeneNameSearch}
                />
            )}
        />,
        <Route
            key='interactor'
            path={['/interactor/:ensgId', '/gene/:ensgId']}
            render={props => (
                <InteractorProfile
                    {...props}
                    handleGeneNameSearch={handleGeneNameSearch}
                />
            )}
        />,
        <Route
            key='search'
            path={['/search/:query', '/search']}
            render={props => (
                <SearchResults
                    {...props}
                    setCellLineId={setCellLineId}
                    handleGeneNameSearch={handleGeneNameSearch}
                />
            )}
        />
    ];

    const privateRoutes = [
        <Route
            key='fovs'
            path={['/fovs/:cellLineId', '/fovs']}
            render={props => (
                <TargetProfile
                    {...props}
                    cellLineId={cellLineId}
                    setCellLineId={setCellLineId}
                    showFovAnnotator
                />
            )}
        />,
        <Route
            key='annotations'
            path={['/annotations/:cellLineId', '/annotations']}
            render={props => (
                <TargetProfile
                    {...props}
                    cellLineId={cellLineId}
                    setCellLineId={setCellLineId}
                    showTargetAnnotator
                />
            )}
        />,
        <Route key='umap' path="/umap" component={UMAPContainer}/>,
        <Route key='dashboard' path="/dashboard" component={Dashboard}/>
    ];


    const mainApp = (
        <>
        <Navbar handleGeneNameSearch={handleGeneNameSearch}/>
        <Switch>
            {publicRoutes}
            {modeContext==='private' ? privateRoutes : null}

            <Route path="/gallery" component={Gallery}/>
            <Route path="/about" component={About}/>
            <Route path="/help" component={Help}/>
            <Route path="/download" component={Download}/>
            <Route path="/privacy" component={Privacy}/>
            <Route path="/contact" component={Contact}/>
            <Route path="/jobs" component={Jobs}/>

            <Route><div className="f2 pa3 w-100 ma">Page not found</div></Route>
        </Switch>
        </>
    );

    return (
        <>
        <Switch>
            <Route path="/" exact={true} render={props => (
                <Home {...props} handleGeneNameSearch={handleGeneNameSearch}/>
            )}/>
            <Route>{mainApp}</Route>
        </Switch>
        <Footer/>
        </>
    );
}


let appMode = settings.defaultAppMode;

// only allow setting the appMode from the URL if the defaultAppMode is 'private'
const urlParams = new URLSearchParams(window.location.search);
if (appMode==='private') appMode = urlParams.get('mode') || appMode;


ReactDOM.render(
    <BrowserRouter>
        <settings.ModeContext.Provider value={appMode}>
            <App/>
        </settings.ModeContext.Provider>
    </BrowserRouter>,
    document.getElementById('root')
);
