const RulesDataStoreManager = {
    DataStore: null,
    IsLoading: false,
    LoadPromise: null,
    CacheExpirationMilliseconds: 604800000,
    CacheDataKey: "RulesDataStoreDND5thEdition",
    CacheTimestampKey: "RulesDataStoreDND5thEditionTimestamp",

    Initialize: function () {
        window.RulesDataStoreManager = this;
        const IsHardReload = Boolean(document.querySelector('meta[name="ClientHardReload"]'));
        if (IsHardReload) {
            this.ClearCache();
        }
    },

    ClearCache: function () {
        try {
            localStorage.removeItem(this.CacheDataKey);
            localStorage.removeItem(this.CacheTimestampKey);
        } catch (StorageError) {
        }
        this.DataStore = null;
    },

    PreloadDataStore: function () {
        if (this.DataStore) {
            return Promise.resolve(this.DataStore);
        }
        if (this.LoadPromise) {
            return this.LoadPromise;
        }

        const IsHardReload = Boolean(document.querySelector('meta[name="ClientHardReload"]'));
        if (!IsHardReload) {
            try {
                const CachedTimestampString = localStorage.getItem(this.CacheTimestampKey);
                const CachedDataString = localStorage.getItem(this.CacheDataKey);
                if (CachedTimestampString && CachedDataString) {
                    const CachedTimestamp = parseInt(CachedTimestampString, 10);
                    const CurrentTimestamp = Date.now();
                    if ((CurrentTimestamp - CachedTimestamp) < this.CacheExpirationMilliseconds) {
                        this.DataStore = JSON.parse(CachedDataString);
                        if (typeof SystemDebugger !== "undefined") {
                            SystemDebugger.LogMessage("DEBUG", "Rules Data Store Loaded from Local Storage");
                        }
                        return Promise.resolve(this.DataStore);
                    }
                }
            } catch (StorageReadError) {
            }
        }

        this.IsLoading = true;
        this.LoadPromise = fetch("/API/Characters/Rules/DataStore")
            .then((Response) => {
                if (!Response.ok) {
                    throw new Error("HTTP error " + Response.status);
                }
                return Response.json();
            })
            .then((LoadedDataStore) => {
                this.DataStore = LoadedDataStore;
                this.IsLoading = false;
                try {
                    localStorage.setItem(this.CacheDataKey, JSON.stringify(LoadedDataStore));
                    localStorage.setItem(this.CacheTimestampKey, String(Date.now()));
                } catch (StorageWriteError) {
                }
                if (typeof SystemDebugger !== "undefined") {
                    SystemDebugger.LogMessage("DEBUG", "Rules Data Store Fetched and Cached");
                }
                return this.DataStore;
            })
            .catch((FetchError) => {
                this.IsLoading = false;
                this.LoadPromise = null;
                if (typeof SystemDebugger !== "undefined") {
                    SystemDebugger.LogMessage("DEBUG", "Rules Data Store Fetch Failed: " + FetchError.message);
                }
                return null;
            });

        return this.LoadPromise;
    },

    GetCategoryCandidates: function (CategoryName) {
        if (!this.DataStore) {
            return [];
        }
        const CategoryCandidates = this.DataStore[CategoryName];
        if (Array.isArray(CategoryCandidates)) {
            return CategoryCandidates;
        }
        return [];
    },

    FindCanonicalMatch: function (CategoryName, QueryString) {
        if (!QueryString) {
            return null;
        }
        const CleanQuery = QueryString.trim().toLowerCase();
        if (!CleanQuery) {
            return null;
        }
        const Candidates = this.GetCategoryCandidates(CategoryName);
        for (let Index = 0; Index < Candidates.length; Index += 1) {
            const Candidate = Candidates[Index];
            if (Candidate.toLowerCase() === CleanQuery) {
                return Candidate;
            }
        }
        return null;
    },

    CalculateLevenshteinDistance: function (FirstString, SecondString) {
        const FirstLength = FirstString.length;
        const SecondLength = SecondString.length;
        if (FirstLength === 0) {
            return SecondLength;
        }
        if (SecondLength === 0) {
            return FirstLength;
        }
        const Matrix = [];
        for (let RowIndex = 0; RowIndex <= FirstLength; RowIndex += 1) {
            Matrix[RowIndex] = [RowIndex];
        }
        for (let ColumnIndex = 0; ColumnIndex <= SecondLength; ColumnIndex += 1) {
            Matrix[0][ColumnIndex] = ColumnIndex;
        }
        for (let RowIndex = 1; RowIndex <= FirstLength; RowIndex += 1) {
            for (let ColumnIndex = 1; ColumnIndex <= SecondLength; ColumnIndex += 1) {
                const Cost = FirstString[RowIndex - 1] === SecondString[ColumnIndex - 1] ? 0 : 1;
                Matrix[RowIndex][ColumnIndex] = Math.min(
                    Matrix[RowIndex - 1][ColumnIndex] + 1,
                    Matrix[RowIndex][ColumnIndex - 1] + 1,
                    Matrix[RowIndex - 1][ColumnIndex - 1] + Cost
                );
            }
        }
        return Matrix[FirstLength][SecondLength];
    },

    CalculateSimilarityScore: function (QueryString, CandidateString) {
        const NormalizedQuery = QueryString.toLowerCase().trim();
        const NormalizedCandidate = CandidateString.toLowerCase().trim();
        if (NormalizedQuery === NormalizedCandidate) {
            return 1.0;
        }
        if (NormalizedCandidate.startsWith(NormalizedQuery)) {
            return 0.95;
        }
        if (NormalizedCandidate.includes(" " + NormalizedQuery)) {
            return 0.9;
        }
        if (NormalizedCandidate.includes(NormalizedQuery)) {
            return 0.8;
        }
        const MaximumLength = Math.max(NormalizedQuery.length, NormalizedCandidate.length);
        if (MaximumLength === 0) {
            return 1.0;
        }
        const EditDistance = this.CalculateLevenshteinDistance(NormalizedQuery, NormalizedCandidate);
        return 1.0 - (EditDistance / MaximumLength);
    },

    FindSuggestions: function (CategoryName, QueryString, MaximumResults = 3) {
        if (!QueryString) {
            return [];
        }
        const CleanQuery = QueryString.trim();
        if (CleanQuery.length < 2) {
            return [];
        }
        const ExactMatch = this.FindCanonicalMatch(CategoryName, CleanQuery);
        if (ExactMatch && ExactMatch.toLowerCase() === CleanQuery.toLowerCase() && ExactMatch === CleanQuery) {
            return [];
        }
        const Candidates = this.GetCategoryCandidates(CategoryName);
        const ScoredMatches = [];
        for (let Index = 0; Index < Candidates.length; Index += 1) {
            const Candidate = Candidates[Index];
            const Score = this.CalculateSimilarityScore(CleanQuery, Candidate);
            if (Score >= 0.6) {
                ScoredMatches.push({
                    Candidate: Candidate,
                    Score: Score
                });
            }
        }
        ScoredMatches.sort((FirstMatch, SecondMatch) => SecondMatch.Score - FirstMatch.Score);
        const Results = [];
        for (let Index = 0; Index < Math.min(ScoredMatches.length, MaximumResults); Index += 1) {
            Results.push(ScoredMatches[Index].Candidate);
        }
        return Results;
    }
};

$(document).ready(() => {
    RulesDataStoreManager.Initialize();
});
