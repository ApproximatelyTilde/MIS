const RulesDataStoreManager = {
    DataStore: null,
    IsLoading: false,
    LoadPromise: null,
    CacheExpirationMilliseconds: 604800000,
    CacheDataKey: "RulesDataStoreDND5E_v2",
    CacheTimestampKey: "RulesDataStoreDND5ETimestamp_v2",

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

    GetSpeciesTraits: function (SpeciesName) {
        if (!this.DataStore || !SpeciesName) {
            return [];
        }
        const CleanKey = SpeciesName.trim().toLowerCase();
        const SpeciesMap = this.DataStore["SpeciesFeaturesMap"] || {};
        return SpeciesMap[CleanKey] || [];
    },

    GetBackgroundFeatures: function (BackgroundName) {
        if (!this.DataStore || !BackgroundName) {
            return [];
        }
        const CleanKey = BackgroundName.trim().toLowerCase();
        const BackgroundMap = this.DataStore["BackgroundFeaturesMap"] || {};
        return BackgroundMap[CleanKey] || [];
    },

    GetSubclassesForClass: function (ClassName) {
        if (!this.DataStore || !ClassName) {
            return [];
        }
        const CleanKey = ClassName.trim().toLowerCase();
        const SubclassesMap = this.DataStore["ClassSubclassesMap"] || {};
        return SubclassesMap[CleanKey] || [];
    },

    IsGenericProgressionFeature: function (FeatureName) {
        if (!FeatureName) {
            return false;
        }
        const CleanName = FeatureName.trim().toLowerCase();
        const GenericProgressionNames = [
            "ability score improvement",
            "ability score increase",
            "epic boon",
            "epic boon feat",
            "subclass feature"
        ];
        if (GenericProgressionNames.includes(CleanName)) {
            return true;
        }

        if (CleanName.endsWith("subclass")) {
            return true;
        }

        if (CleanName.endsWith("feature") && (CleanName.includes("subclass") || CleanName.includes("tradition") || CleanName.includes("archetype") || CleanName.includes("domain") || CleanName.includes("college") || CleanName.includes("circle") || CleanName.includes("oath") || CleanName.includes("origin") || CleanName.includes("patron") || CleanName.includes("path"))) {
            return true;
        }

        if (CleanName.includes("improvement") || CleanName.includes("improvements")) {
            return true;
        }

        return false;
    },

    GetClassFeatures: function (ClassName, ClassLevel, SubclassName) {
        if (!this.DataStore || !ClassName) {
            return [];
        }
        const CleanClassKey = ClassName.trim().toLowerCase();
        const LevelNumber = parseInt(ClassLevel, 10) || 1;
        const ClassFeaturesMap = this.DataStore["ClassFeaturesMap"] || {};
        const LevelMap = ClassFeaturesMap[CleanClassKey] || {};
        const ResultFeatures = [];
        for (let LevelIndex = 1; LevelIndex <= LevelNumber; LevelIndex += 1) {
            const LevelKey = LevelIndex.toString();
            const FeaturesForLevel = LevelMap[LevelKey] || [];
            for (let FeatureIndex = 0; FeatureIndex < FeaturesForLevel.length; FeatureIndex += 1) {
                const FeatureName = FeaturesForLevel[FeatureIndex];
                if ((!this.IsGenericProgressionFeature(FeatureName)) && (!ResultFeatures.includes(FeatureName))) {
                    ResultFeatures.push(FeatureName);
                }
            }
        }
        if (SubclassName) {
            const CleanSubclassKey = SubclassName.trim().toLowerCase();
            const SubclassFeaturesMap = this.DataStore["SubclassFeaturesMap"] || {};
            let TargetSubclassMap = SubclassFeaturesMap[`${CleanClassKey}:${CleanSubclassKey}`];
            if (!TargetSubclassMap) {
                const AllSubclasses = this.GetSubclassesForClass(ClassName);
                for (let SubclassIndex = 0; SubclassIndex < AllSubclasses.length; SubclassIndex += 1) {
                    const CandidateName = AllSubclasses[SubclassIndex];
                    if (CandidateName.toLowerCase() === CleanSubclassKey) {
                        TargetSubclassMap = SubclassFeaturesMap[`${CleanClassKey}:${CandidateName.toLowerCase()}`];
                        break;
                    }
                }
            }
            if (TargetSubclassMap) {
                for (let LevelIndex = 1; LevelIndex <= LevelNumber; LevelIndex += 1) {
                    const LevelKey = LevelIndex.toString();
                    const SubclassFeaturesForLevel = TargetSubclassMap[LevelKey] || [];
                    for (let FeatureIndex = 0; FeatureIndex < SubclassFeaturesForLevel.length; FeatureIndex += 1) {
                        const FeatureName = SubclassFeaturesForLevel[FeatureIndex];
                        if ((!this.IsGenericProgressionFeature(FeatureName)) && (!ResultFeatures.includes(FeatureName))) {
                            ResultFeatures.push(FeatureName);
                        }
                    }
                }
            }
        }
        return ResultFeatures;
    },

    Is5EToolsFeature: function (FeatureName) {
        if (!this.DataStore || !FeatureName) {
            return false;
        }
        const CleanName = FeatureName.trim().toLowerCase();
        const AllFeatures = this.DataStore["Features"] || [];
        for (let Index = 0; Index < AllFeatures.length; Index += 1) {
            if (AllFeatures[Index].toLowerCase() === CleanName) {
                return true;
            }
        }
        return false;
    },

    FindCanonicalMatch: function (CategoryNameOrCandidates, QueryString) {
        if (!QueryString) {
            return null;
        }
        const CleanQuery = QueryString.trim().toLowerCase();
        if (!CleanQuery) {
            return null;
        }
        const Candidates = Array.isArray(CategoryNameOrCandidates) ? CategoryNameOrCandidates : this.GetCategoryCandidates(CategoryNameOrCandidates);
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

    FindSuggestions: function (CategoryNameOrCandidates, QueryString, MaximumResults = 3) {
        if (!QueryString) {
            return [];
        }
        const CleanQuery = QueryString.trim();
        if (CleanQuery.length < 2) {
            return [];
        }
        const ExactMatch = this.FindCanonicalMatch(CategoryNameOrCandidates, CleanQuery);
        if (ExactMatch && ExactMatch.toLowerCase() === CleanQuery.toLowerCase() && ExactMatch === CleanQuery) {
            return [];
        }
        const Candidates = Array.isArray(CategoryNameOrCandidates) ? CategoryNameOrCandidates : this.GetCategoryCandidates(CategoryNameOrCandidates);
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
