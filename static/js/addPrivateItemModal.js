$(document).ready(function() {
    $("#create-new-item-button").on("click", function(evt) {
        var list = $(this).data("list");
        $("#list-title").val(list);
        $("#add-bucket-list-item").modal("show");
    });
//     $("#private-item-form").on("submit", function(evt) {
//         evt.preventDefault();

//         var formData = new FormData();
//         var file = document.getElementById("image").files[0];

//         formData.append("file", file);

//         var list = $("#list-title").val();
//         var lat = $("#lat").val();
//         var lon = $("#lon").val();
//         var title = $("#title").val();
//         var image = $("#image").val();
//         console.log(image);
//         var tourLink = $("#tour-link").val();
//         var description = $("#description").val();

//         $.ajax({
//             type: "POST",
//             url: '/fileupload',
//             data: formData,
//             dataType: 'json',
//             contentType: false,
//             processData: false,
//             success: function (response) {
//             $.ajax({
//             type: "POST",
//             url: '/add-item/process',
//             data: {"title": title, "tour_link": tourLink, 
//                    "image": response, "latitude": lat, 
//                    "longitude": lon, "description": description,
//                    "list": list},
//             dataType: 'json',
//             contentType: false,
//             processData: false,
//             success: function (response) {
//             if (response === "Item Added") {
//                         $("#add-bucket-list-item").modal("hide");
//                       } else {
//                         console.log("You already have a list with that title");
//                       }
//             }
//             });  
//             }
//         });
//     });

  });



