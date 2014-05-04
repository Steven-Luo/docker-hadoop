'use strict';

var underscore = angular.module('underscore', []);
underscore.factory('_', function() {
  return window._;
});

var dashboardApp = angular.module('dashboardApp', ['ui.bootstrap', 'underscore']); 

dashboardApp.controller('MainCtrl', function($scope, $window, $filter, $modal, $timeout, $http, _) {
        
    $scope.cluster = [];
    $scope.selectedNode = undefined;
    $scope.selectedNodeId = undefined;
    $scope.notification = {msg: undefined, type: undefined, timeout: undefined};

    $scope.$watch('notification', function(newNotification) {
        if (newNotification.timeout && newNotification.timeout != -1 && newNotification.timeout != 0) {
            $timeout(function(){
                if ($scope.notification.msg == newNotification.msg) {
                    $scope.notification.type = undefined;
                }
            }, newNotification.timeout * 1000);
        }
    });

    $scope.init = function() {
        getCluster();
    }

    function getCluster() {
        $http.get("/json/cluster").success(function(data) {
            console.log("/json/cluster result:", data);
            $scope.cluster = data.nodes;
        }).error(function(data) {
            $scope.notification = {msg: "Error getting cluster nodes: " + JSON.stringify(data), type: "error", timeout: 15};
        });
    }

    function checkStartingNodes() {
        var startingNodes = _.filter($scope.cluster, {node_status: "starting"});
        console.log("checkStartingNodes: startingNodes:", startingNodes);
        if (startingNodes && startingNodes.length > 0) {
            console.log("Found starting. Refreshing in two second.");
            $timeout(function() {
                getCluster();
            }, 2000);
        }
    }

    $scope.$watch("cluster", function(newClusterNodes, oldClusterNodes) {
        if (!_.isEqual(newClusterNodes, oldClusterNodes)) {
            checkStartingNodes();
        }
    });

    $scope.stopCluster = function() {

        $scope.notification = {msg: "Stopping cluster...", type: "warning"};
        $http.post("/stop-cluster").success(function(data) {
            console.log("Stopped cluster. Updating cluster nodes.");
            getCluster();
            $scope.notification = {msg: "Cluster stopped.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while stopping cluster.", data);
            $scope.notification = {msg: "Error while stopping cluster: " + JSON.stringify(data), type: "error", timeout: 15};
        });
    }

    $scope.stopContainer = function(containerId) {
        $scope.notification = {msg: "Stopping container " + containerId + "...", type: "warning"};
        $http.post("/container/" + containerId + "/stop").success(function(data) {
            getCluster();
            $scope.notification = {msg: "Node " + containerId + " stopped.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while stopping node", containerId, data);
            $scope.notification = {msg: "Error while stopping node " + containerId + " : " + JSON.stringify(data), type: "error", timeout: 15};
        })
    }

    $scope.selectNode = function(containerId) {
        $scope.selectedNodeId = containerId; 
    }

    /// Logica de detalle de nodo.

    $scope.$watch("selectedNodeId", function(newNodeId, oldNodeId) {
        console.log("selectedNodeId change: ", newNodeId, oldNodeId);
        if (!_.isEqual(newNodeId, oldNodeId)) {
            getNodeDetails($scope.selectedNodeId);
        }
    })

    function getNodeDetails(nodeId) {
        $http.get("/json/container/" + nodeId).success(function(data) {
            $scope.selectedNode = data;
        }).error(function(data) {
            console.log("Errow while ladoing node", nodeId, data);
            $scope.notification = {msg: "Error while loading node " + nodeId + " details: " + JSON.stringify(data), type: "error", timeout: 15};
        });
    }


    /// Logica de Inicio de cluster.

    $scope.possibleImages = ["vierja/hadoop", "vierja/hadoop2"];

    var nodeTemplate = {
        image:  $scope.possibleImages[0],
        hostname: "hadoop",
        ip: "10.0.10.",
        services: []
    }

    // Genero la lista inicial de nodos.
    $scope.newCluster = [];
    for (var i = 1; i < 6; i++) {
        addNewNode(i);
    }

    function addNewNode(index) {
        var newNode = _.clone(nodeTemplate, true);
        newNode.hostname += index;
        newNode.ip += index;
        if (index == 1) {
            newNode.services = ["JOBTRACKER"];
        } else if (index == 2) {
            newNode.services = ["NAMENODE"];
        } else if (index == 3) {
            newNode.services = ["SECONDARYNAMENODE"];
        } else {
            newNode.services = ["TASKTRACKER", "DATANODE"];
        }
        $scope.newCluster.push(newNode);
    }

    $scope.possibleServices = [
        {
            "name": "JobTracker",
            "value": "JOBTRACKER",
        },
        {
            "name": "NameNode",
            "value": "NAMENODE",
        },
        {
            "name": "Secondary NameNode",
            "value": "SECONDARYNAMENODE",
        },
        {
            "name": "TaskTracker",
            "value": "TASKTRACER",
        },
        {
            "name": "DataNode",
            "value": "DATANODE",
        },
    ];

    $scope.startCluster = function() {
        $scope.notification = {msg: "Starting cluster...", type: "warning"};
        console.log("Start cluster:", $scope.newCluster);
        $http.post("/json/start-cluster", $scope.newCluster).success(function(data) {
            console.log("start cluster response", data);
            getCluster();
            $scope.notification = {msg: "Cluster with " + data.nodes_started + " nodes started.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("start cluster error response", data);
            $scope.notification = {msg: "Error starting cluster: " + JSON.stringify(data), type: "error", timeout: 15};
        })
    }

    $scope.newRow = function() {
        console.log("newRow for cluster:", $scope.newCluster, "length:", $scope.newCluster.length);
        addNewNode($scope.newCluster.length + 1);
    }

    $scope.delLastRow = function() {
        $scope.newCluster.pop();
    }
});


dashboardApp.directive('ngSelectPicker', ['$timeout', '$parse', function($timeout, $parse) {
  return {
    link: function($scope, elt, attrs) {
      var refresh = function() {
        $(elt).selectpicker('refresh');
      }
      $timeout(refresh, 0);
    }   
  }     
}])
