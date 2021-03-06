var gulp = require('gulp');
var sass = require('gulp-sass');
var jshint = require('gulp-jshint');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var imagemin = require('gulp-imagemin');
var plumber = require('gulp-plumber');
var notify = require('gulp-notify');
var autoprefixer = require('gulp-autoprefixer');
var rename = require('gulp-rename');

var plumberErrorHandler = { errorHandler: notify.onError({
    title: 'Gulp',
    message: 'Error: <%= error.message %>'
  })
};
 
gulp.task('sass', function () { 
    gulp.src('sass/*.sass')
    	.pipe(plumber(plumberErrorHandler))
        .pipe(sass({ outputStyle: 'compressed', includePaths: ['node_modules'] }))
        .pipe(autoprefixer({
            browsers: ['last 2 versions'],
            cascade: false
        }))
        .pipe(rename('main.css'))
 		.pipe(gulp.dest('../static/css'))
        .pipe(notify('styles reloaded'))
});

gulp.task('libs', function () {
    gulp.src([
        './node_modules/jquery/dist/jquery.js', 
        './node_modules/moment/min/moment.min.js', 
        './node_modules/bootstrap/dist/js/bootstrap.js', 
        './node_modules/datatables.net/js/jquery.dataTables.js', 
        './node_modules/datatables.net-bs4/js/dataTables.bootstrap4.js', 
        './node_modules/bootstrap-cookie-alert/cookiealert.js', 
        './node_modules/prismjs/prism.js', 
        'js/libs/*.js'
        ])
        // .pipe(jshint())
        // .pipe(jshint.reporter('default'))
        .pipe(concat('main-libs.js'))
        // .pipe(uglify())
        .pipe(gulp.dest('../static/js'))
        .pipe(notify('libs reloaded'))
});

gulp.task('scripts', function () {
    gulp.src(['js/scripts/*.js'])
        // .pipe(jshint())
        // .pipe(jshint.reporter('default'))
        .pipe(concat('main-scripts.js'))
        // .pipe(uglify())
        .pipe(gulp.dest('../static/js'))
        .pipe(notify('scripts reloaded'))
});

gulp.task('fonts', function () {
    gulp.src(['fonts/*'])
        .pipe(gulp.dest('../static/fonts'))
});

gulp.task('img', function() {
  gulp.src('img/**/*.{png,jpg,gif,svg}')
    .pipe(imagemin({
    	optimizationLevel: 7,
 		progressive: true
    }))
    .pipe(gulp.dest('../static/img'))
});

gulp.task('watch', function() {
	gulp.watch('sass/**/*.{sass,scss}', ['sass']);
	gulp.watch('js/libs/*.js', ['libs']);
	gulp.watch('js/scripts/*.js', ['scripts']);
	gulp.watch('img/*.{png,jpg,gif,svg}', ['img']);
    gulp.watch('fonts/*', ['fonts']);
});

gulp.task('default', ['sass', 'libs', 'img', 'scripts', 'fonts', 'watch']);