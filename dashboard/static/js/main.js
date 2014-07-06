'use strict';

var underscore = angular.module('underscore', []);
underscore.factory('_', function() {
  return window._;
});

var dashboardApp = angular.module('dashboardApp', ['ui.bootstrap', 'underscore']); 

dashboardApp.controller('MainCtrl', function($scope, $window, $filter, $modal, $timeout, $http, _) {
        
    $scope.cluster = undefined;
    $scope.selectedNode = undefined;
    $scope.selectedNodeId = undefined;
    $scope.notification = {msg: undefined, type: undefined, timeout: undefined};

    function cleanNotification() {
        $scope.notification.type = undefined;
    }

    $scope.$watch('notification', function(newNotification) {
        if (newNotification.timeout && newNotification.timeout != -1 && newNotification.timeout != 0) {
            $timeout(function(){
                if ($scope.notification.msg == newNotification.msg) {
                    cleanNotification();
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
        $http.post("/json/cluster/kill").success(function(data) {
            console.log("Stopped cluster. Updating cluster nodes.");
            $scope.cluster = undefined;
            getCluster();
            $scope.notification = {msg: "Cluster stopped.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while stopping cluster.", data);
            $scope.notification = {msg: "Error while stopping cluster: " + JSON.stringify(data), type: "error", timeout: 15};
        });
    }

    $scope.stopContainer = function(containerId) {
        $scope.notification = {msg: "Stopping container " + containerId + "...", type: "warning"};
        $http.post("/json/container/" + containerId + "/stop").success(function(data) {
            getCluster();
            $scope.notification = {msg: "Node " + containerId + " stopped.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while stopping node", containerId, data);
            $scope.notification = {msg: "Error while stopping node " + containerId + " : " + JSON.stringify(data), type: "error", timeout: 15};
        })
    }

    $scope.killContainer = function(containerId) {
        $scope.notification = {msg: "Killing container " + containerId + "...", type: "warning"};
        $http.post("/json/container/" + containerId + "/kill").success(function(data) {
            getCluster();
            $scope.notification = {msg: "Node " + containerId + " killed.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while killing node", containerId, data);
            $scope.notification = {msg: "Error while killing node " + containerId + " : " + JSON.stringify(data), type: "error", timeout: 15};
        })
    }

    $scope.startContainer = function(containerId) {
        $scope.notification = {msg: "Unpausing container " + containerId + "...", type: "warning"};
        $http.post("/json/container/" + containerId + "/start").success(function(data) {
            getCluster();
            $scope.notification = {msg: "Node " + containerId + " started.", type: "success", timeout: 6};
        }).error(function(data) {
            console.log("Errow while unpausing node", containerId, data);
            $scope.notification = {msg: "Error while unpausing node " + containerId + " : " + JSON.stringify(data), type: "error", timeout: 15};
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
            $scope.selectedNode.serviceList = [];
            $scope.selectedNode.services.split(',').forEach(function(se) {
                $scope.selectedNode.serviceList.push(se.trim());
            })
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
        $http.post("/json/cluster/start", $scope.newCluster).success(function(data) {
            console.log("start cluster response", data);
            $scope.cluster = undefined;
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

    $scope.showLogs = false;
    $scope.nodeLogs = "";
    $scope.nodeLogsLastNow = 0;
    $scope.nodeLogsLines = 1000;

    function loadLogs(containerId, service, lines) {
        console.log("loadLogs(", containerId, service, lines, ")");
        if ($scope.showLogs) {
            $timeout(function(){
                loadLogs($scope.selectedNode.ID.substring(0,12), $scope.nodeLogsService.toLowerCase(), $scope.nodeLogsLines);
            }, 800);
            var now = new Date().getTime();
            $http.get("/json/container/" + containerId + "/" + service + "/logs?now=" + now).success(function(data) {
                if ($scope.nodeLogsLastNow < now) {
                    $scope.nodeLogsLastNow = now;
                    $scope.nodeLogs = data.logs;
                }
            }, function(data) {
                console.log("Error gettings logs for container", containerId, "and service", service);
            });
        }
    }

    $scope.$watch("showLogs", function() {
        console.log("Change in showLogs", $scope.showLogs);
        if ($scope.selectedNode) {
            console.log("nodeLogsService:", $scope.nodeLogsService);
            loadLogs($scope.selectedNode.ID.substring(0,12), $scope.nodeLogsService.toLowerCase());
        }
    })

    $scope.updateServices = function() {
        $http.post("/json/cluster/update_services").success(function(data) {
            getCluster();
        }).error(function(data) {
            console.log("Errow while updating services:", data);
        })
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
